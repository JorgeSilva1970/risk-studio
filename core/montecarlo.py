"""Quantitative risk analysis: Monte Carlo (PERT / Bernoulli with Gaussian-copula
correlation) for the risk register, and FAIR (Factor Analysis of Information Risk)
for cyber / loss-event scenarios."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtr

from core.catalogs import PROB_SCALE


def pert_sample(rng: np.random.Generator, lo, ml, hi, size, lam: float = 4.0) -> np.ndarray:
    lo, ml, hi = float(lo), float(ml), float(hi)
    if hi < lo:
        lo, hi = hi, lo
    ml = min(max(ml, lo), hi)
    if hi - lo < 1e-12:
        return np.full(size, lo)
    a = 1 + lam * (ml - lo) / (hi - lo)
    b = 1 + lam * (hi - ml) / (hi - lo)
    return lo + rng.beta(a, b, size) * (hi - lo)


def pert_mean(lo, ml, hi, lam: float = 4.0) -> float:
    return (lo + lam * ml + hi) / (lam + 2)


def impact_band(level: int, thresholds: list[float]) -> tuple[float, float, float]:
    """Default € (min, most likely, max) for an impact level, from the impact scale thresholds."""
    t = [0.0] + [float(x) for x in thresholds]
    level = int(min(5, max(1, level)))
    lo, hi = t[level - 1], t[level]
    if level == 1:
        lo = hi * 0.1
    ml = lo + (hi - lo) * 0.4
    return lo, ml, hi


def build_inputs(risks_analysed: pd.DataFrame, thresholds: list[float]) -> pd.DataFrame:
    """Per-risk quantitative inputs (inherent and residual)."""
    rows = []
    for r in risks_analysed.to_dict(orient="records"):
        if r.get("status") == "closed":
            continue
        opp = r.get("type") == "opportunity"
        p_inh, i_inh = int(r["p_inh"]), int(r["i_inh"])
        p_res, i_res = int(r["p_res"]), int(r["i_res"])
        pp = r.get("prob_pct")
        has_p = pp is not None and not pd.isna(pp)
        prob_inh = float(pp) / 100 if has_p else PROB_SCALE[p_inh][2]
        prob_inh = min(0.999, max(0.0, prob_inh))
        prob_res = prob_inh * PROB_SCALE[p_res][2] / PROB_SCALE[p_inh][2]
        vals = [r.get("imp_min"), r.get("imp_ml"), r.get("imp_max")]
        if all(v is not None and not pd.isna(v) for v in vals):
            lo, ml, hi = (float(v) for v in vals)
            src = "user"
        else:
            lo, ml, hi = impact_band(i_inh, thresholds)
            src = "scale"
        k = i_res / i_inh if i_inh else 1.0
        sign = -1.0 if opp else 1.0
        rows.append({
            "id": r["id"], "title": r.get("title", ""), "type": r.get("type"), "category": r.get("category"),
            "prob_inh": prob_inh, "prob_res": min(0.999, prob_res), "lo": lo, "ml": ml, "hi": hi,
            "k_res": k, "sign": sign, "source": src,
            "ev_inh": sign * prob_inh * pert_mean(lo, ml, hi),
            "ev_res": sign * min(0.999, prob_res) * pert_mean(lo, ml, hi) * k,
        })
    return pd.DataFrame(rows)


def simulate(inputs: pd.DataFrame, n: int = 10_000, rho: float = 0.0, seed: int = 42,
             residual: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Return (total net loss per iteration, matrix of per-risk outcomes [n × k])."""
    rng = np.random.default_rng(seed)
    k = len(inputs)
    if k == 0:
        return np.zeros(n), np.zeros((n, 0))
    rho = float(min(0.95, max(0.0, rho)))
    z_common = rng.standard_normal((n, 1))
    z_ind = rng.standard_normal((n, k))
    z = np.sqrt(rho) * z_common + np.sqrt(1 - rho) * z_ind
    u = ndtr(z)
    probs = inputs["prob_res" if residual else "prob_inh"].to_numpy()
    occur = u < probs
    mat = np.zeros((n, k))
    for j, row in enumerate(inputs.itertuples(index=False)):
        imp = pert_sample(rng, row.lo, row.ml, row.hi, n)
        if residual:
            imp = imp * row.k_res
        mat[:, j] = occur[:, j] * imp * row.sign
    return mat.sum(axis=1), mat


def stats(total: np.ndarray, capacity: float | None = None) -> dict:
    if total.size == 0:
        return {}
    q = np.percentile(total, [5, 10, 50, 80, 90, 95, 99])
    var95 = q[5]
    tail = total[total >= var95]
    out = {
        "mean": float(total.mean()), "std": float(total.std()),
        "p5": float(q[0]), "p10": float(q[1]), "p50": float(q[2]), "p80": float(q[3]),
        "p90": float(q[4]), "p95": float(var95), "p99": float(q[6]),
        "cvar95": float(tail.mean()) if tail.size else float(var95),
        "max": float(total.max()), "min": float(total.min()),
        "p_loss": float((total > 0).mean()),
    }
    if capacity:
        out["p_exceed_capacity"] = float((total > capacity).mean())
    return out


def sensitivity(mat: np.ndarray, total: np.ndarray, inputs: pd.DataFrame) -> pd.DataFrame:
    """Spearman rank correlation of each risk with the total + mean contribution."""
    if mat.shape[1] == 0:
        return pd.DataFrame(columns=["id", "title", "corr", "mean", "share"])
    rt = pd.Series(total).rank().to_numpy()
    corrs = []
    for j in range(mat.shape[1]):
        col = mat[:, j]
        if np.std(col) < 1e-12:
            corrs.append(0.0)
            continue
        rc = pd.Series(col).rank().to_numpy()
        corrs.append(float(np.corrcoef(rc, rt)[0, 1]))
    means = mat.mean(axis=0)
    tot = np.abs(means).sum() or 1.0
    df = pd.DataFrame({"id": inputs["id"], "title": inputs["title"], "corr": corrs,
                       "mean": means, "share": np.abs(means) / tot})
    return df.sort_values("corr", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)


# -------------------------------------------------------------------- FAIR
def simulate_fair(sc: dict, n: int = 10_000, seed: int = 7) -> dict:
    """FAIR: LEF = TEF × Vulnerability; Loss = Σ (Primary + SLEF × Secondary) per event.
    Returns annualised loss distribution and components."""
    rng = np.random.default_rng(seed)
    tef = pert_sample(rng, sc["tef_min"], sc["tef_ml"], sc["tef_max"], n)
    vuln = np.clip(pert_sample(rng, sc["vuln_min"], sc["vuln_ml"], sc["vuln_max"], n), 0, 1)
    lef = tef * vuln
    events = rng.poisson(lef)
    total_events = int(events.sum())
    ale = np.zeros(n)
    if total_events > 0:
        plm = pert_sample(rng, sc["plm_min"], sc["plm_ml"], sc["plm_max"], total_events)
        sec = rng.random(total_events) < float(sc.get("slef") or 0)
        slm = pert_sample(rng, sc["slm_min"], sc["slm_ml"], sc["slm_max"], total_events) * sec
        idx = np.repeat(np.arange(n), events)
        ale = np.bincount(idx, weights=plm + slm, minlength=n)
    return {"ale": ale, "lef": lef, "tef": tef, "vuln": vuln, "events": events}


def exceedance_curve(values: np.ndarray, points: int = 60) -> pd.DataFrame:
    if values.size == 0:
        return pd.DataFrame(columns=["loss", "prob"])
    xs = np.linspace(0, np.percentile(values, 99.5), points)
    probs = [(values > x).mean() for x in xs]
    return pd.DataFrame({"loss": xs, "prob": probs})
