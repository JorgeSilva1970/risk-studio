"""Rule-based interpretation of each module (works without AI)."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from core import scoring
from core.catalogs import label
from core.i18n import L
from core.model import ids_list


def _ids(df: pd.DataFrame, n: int = 6) -> str:
    v = list(df["id"])
    return ", ".join(v[:n]) + (f" (+{len(v) - n})" if len(v) > n else "")


def matrix(p: dict) -> list[str]:
    ra = scoring.analyse_risks(p)
    if ra.empty:
        return []
    thr = ra[ra["type"] == "threat"]
    out = []
    crit_i, crit_r = thr[thr["score_inh"] >= 15], thr[thr["score_res"] >= 15]
    out.append(L(f"Riscos críticos: **{len(crit_i)} inerentes → {len(crit_r)} residuais**.",
                 f"Critical risks: **{len(crit_i)} inherent → {len(crit_r)} residual**."))
    static = thr[(thr["score_res"] == thr["score_inh"]) & (thr["score_inh"] >= 8)]
    if not static.empty:
        out.append(L(f"Sem redução apesar de exposição relevante: {_ids(static)} — os controlos não existem, não estão testados ou são ineficazes.",
                     f"No reduction despite material exposure: {_ids(static)} — controls are missing, untested or ineffective."))
    gap = thr[thr["score_tgt"] < thr["score_res"]]
    if not gap.empty:
        out.append(L(f"{len(gap)} risco(s) ainda acima do alvo definido ({_ids(gap)}): confirme que têm ações de tratamento.",
                     f"{len(gap)} risk(s) still above target ({_ids(gap)}): confirm they have treatment actions."))
    fast = thr[(thr["velocity"] >= 4) & (thr["score_res"] >= 9)]
    if not fast.empty:
        out.append(L(f"Riscos rápidos e relevantes ({_ids(fast)}): privilegie controlos detetivos/corretivos e planos de resposta prontos — há pouco tempo para reagir.",
                     f"Fast, material risks ({_ids(fast)}): favour detective/corrective controls and ready response plans — little time to react."))
    opp = ra[ra["type"] == "opportunity"]
    if not opp.empty:
        hi = opp[opp["score_inh"] >= 10]
        out.append(L(f"{len(opp)} oportunidade(s); {len(hi)} de valor elevado — atribua responsável e estratégia de explorar/potenciar.",
                     f"{len(opp)} opportunity(ies); {len(hi)} high-value — assign an owner and an exploit/enhance strategy."))
    return out


def controls(p: dict) -> list[str]:
    ca = scoring.analyse_controls(p)
    cov = scoring.coverage(p)
    if ca.empty:
        return [L("Sem controlos: o registo é apenas meia ferramenta.", "No controls: the register is only half a tool.")]
    out = []
    n = len(ca)
    auto = (ca["nature"] == "automated").mean()
    prev = ca["control_type"].isin(["preventive", "directive"]).mean()
    out.append(L(f"{n} controlos · {auto:.0%} automáticos · {prev:.0%} preventivos/diretivos. "
                 f"Eficácia média {ca['effectiveness'].mean():.0%}.",
                 f"{n} controls · {auto:.0%} automated · {prev:.0%} preventive/directive. Average effectiveness {ca['effectiveness'].mean():.0%}."))
    if prev > 0.8:
        out.append(L("Carteira muito centrada na prevenção: acrescente controlos detetivos/corretivos para quando a prevenção falhar.",
                     "Portfolio heavily preventive: add detective/corrective controls for when prevention fails."))
    elif prev < 0.3:
        out.append(L("Poucos controlos preventivos: a organização está sobretudo a reagir depois de o risco ocorrer.",
                     "Few preventive controls: the organisation mostly reacts after the risk occurs."))
    if len(cov["controls_untested"]):
        out.append(L(f"{len(cov['controls_untested'])} controlo(s) por testar ({_ids(cov['controls_untested'])}) — sem teste, a eficácia é presumida e o residual fica sobrestimado na redução.",
                     f"{len(cov['controls_untested'])} untested control(s) ({_ids(cov['controls_untested'])}) — without testing, effectiveness is assumed."))
    bad = ca[ca["conclusion"].isin(["ineffective", "partial"]) & ~ca["has_action"]]
    if not bad.empty:
        out.append(L(f"Controlos com deficiências e **sem ação de melhoria**: {_ids(bad)} — passo 7 da cadeia em falta.",
                     f"Deficient controls **without an improvement action**: {_ids(bad)} — step 7 of the chain missing."))
    no_ev = ca[ca["evidence"].fillna("") == ""]
    if not no_ev.empty:
        out.append(L(f"Sem evidência definida: {_ids(no_ev)} — não será possível demonstrar o funcionamento a auditores/reguladores.",
                     f"No evidence defined: {_ids(no_ev)} — operation cannot be demonstrated to auditors/regulators."))
    lines = ca["line"].value_counts().to_dict()
    if not lines.get("second"):
        out.append(L("Nenhum controlo de 2.ª linha (risco/compliance): falta supervisão independente da gestão.",
                     "No 2nd-line controls (risk/compliance): independent oversight of management is missing."))
    return out


def treatment(p: dict) -> list[str]:
    acts = scoring.analyse_actions(p)
    ra = scoring.analyse_risks(p)
    out = []
    if acts.empty:
        return [L("Sem plano de ações.", "No action plan.")]
    done = (acts["status"] == "done").mean()
    out.append(L(f"{len(acts)} ações · {done:.0%} concluídas · progresso médio {acts['progress'].mean():.0f}%.",
                 f"{len(acts)} actions · {done:.0%} done · average progress {acts['progress'].mean():.0f}%."))
    od = acts[acts["overdue"]]
    if not od.empty:
        out.append(L(f"⏰ Em atraso: {_ids(od)} — reveja prazos ou escale ao comité de risco.",
                     f"⏰ Overdue: {_ids(od)} — reschedule or escalate to the risk committee."))
    no_owner = acts[acts["owner"].fillna("") == ""]
    if not no_owner.empty:
        out.append(L(f"Ações sem responsável: {_ids(no_owner)}.", f"Actions without an owner: {_ids(no_owner)}."))
    if not ra.empty:
        bad = ra[(ra["type"] == "threat") & (ra["strategy"] == "accept") & (ra["appetite_status"] == "outside")]
        if not bad.empty:
            out.append(L(f"Incoerência: estratégia «Aceitar» em risco fora da tolerância ({_ids(bad)}) — exige aceitação formal pelo órgão de gestão.",
                         f"Inconsistency: 'Accept' strategy on a risk outside tolerance ({_ids(bad)}) — requires formal board acceptance."))
    unknown = acts[~acts["risk_id"].isin(set(p["risks"]["id"]))] if not p["risks"].empty else acts
    if not unknown.empty:
        out.append(L(f"Ações ligadas a riscos inexistentes: {_ids(unknown)}.", f"Actions linked to unknown risks: {_ids(unknown)}."))
    return out


def kris(p: dict) -> list[str]:
    kr = scoring.analyse_kris(p)
    ra = scoring.analyse_risks(p)
    out = []
    if kr.empty:
        return [L("Sem KRIs: a monitorização depende apenas de revisões periódicas.", "No KRIs: monitoring relies only on periodic reviews.")]
    red, amber = kr[kr["rag"] == "red"], kr[kr["rag"] == "amber"]
    if not red.empty:
        out.append(L(f"🔴 {_ids(red)} acima do limiar vermelho — acionar planos de resposta dos riscos {', '.join(sorted(set(red['risk_id'])))}.",
                     f"🔴 {_ids(red)} beyond the red threshold — trigger response plans for risks {', '.join(sorted(set(red['risk_id'])))}."))
    if not amber.empty:
        out.append(L(f"🟡 {_ids(amber)} em alerta.", f"🟡 {_ids(amber)} on warning."))
    worse = kr[kr["trend_calc"] == "up"]
    if not worse.empty:
        out.append(L(f"Tendência a agravar: {_ids(worse)}.", f"Worsening trend: {_ids(worse)}."))
    if not ra.empty:
        top = ra[ra["type"] == "threat"].sort_values("priority", ascending=False).head(5)
        missing = [r for r in top["id"] if r not in set(kr["risk_id"])]
        if missing:
            out.append(L(f"Riscos prioritários sem KRI: {', '.join(missing)}.", f"Priority risks without a KRI: {', '.join(missing)}."))
    return out


def maturity(p: dict) -> list[str]:
    from core.catalogs import MATURITY_DIMENSIONS
    from core.i18n import lang
    m = p["maturity"]
    if m.empty:
        return []
    names = {c: (en if lang() == "en" else pt) for c, pt, en in MATURITY_DIMENSIONS}
    cur, tgt = scoring.maturity_index(p)
    out = [L(f"Índice {cur:.1f}/5 (alvo {tgt:.1f}).", f"Index {cur:.1f}/5 (target {tgt:.1f}).")]
    low = m[m["current"] <= 2]
    if not low.empty:
        out.append(L("Dimensões em nível inicial/repetível: " + ", ".join(names.get(d, d) for d in low["dim"]) + ".",
                     "Dimensions at initial/repeatable level: " + ", ".join(names.get(d, d) for d in low["dim"]) + "."))
    noev = m[(m["current"] >= 4) & (m["evidence"].fillna("") == "")]
    if not noev.empty:
        out.append(L("Classificações ≥ 4 sem evidência registada: " + ", ".join(names.get(d, d) for d in noev["dim"]) + " — risco de sobreavaliação.",
                     "Ratings ≥ 4 without evidence: " + ", ".join(names.get(d, d) for d in noev["dim"]) + " — risk of over-rating."))
    return out


def fmea(p: dict) -> list[str]:
    f = scoring.analyse_fmea(p)
    if f.empty:
        return []
    out = []
    h = f[f["ap"] == "H"]
    out.append(L(f"{len(f)} modos de falha · {len(h)} com prioridade de ação **Alta** ({_ids(h) if len(h) else '—'}).",
                 f"{len(f)} failure modes · {len(h)} with **High** action priority ({_ids(h) if len(h) else '—'})."))
    sev = f[(f["s"] >= 9) & (f["rpn"] < 100)]
    if not sev.empty:
        out.append(L(f"Gravidade muito alta com RPN baixo ({_ids(sev)}): não confie só no RPN — trate pela gravidade.",
                     f"Very high severity with low RPN ({_ids(sev)}): don't rely on RPN alone — act on severity."))
    det = f[f["d"] >= 7]
    if not det.empty:
        out.append(L(f"Deteção fraca (D ≥ 7) em {_ids(det)}: reforçar controlos detetivos.", f"Weak detection (D ≥ 7) in {_ids(det)}: strengthen detective controls."))
    return out


def bowtie(p: dict, rid: str) -> list[str]:
    ca = scoring.analyse_controls(p)
    lc = ca[ca["risk_ids"].apply(lambda s: rid in ids_list(s))] if not ca.empty else ca
    prev = lc[lc["control_type"].isin(["preventive", "directive"])] if not lc.empty else lc
    mit = lc[lc["control_type"].isin(["detective", "corrective"])] if not lc.empty else lc
    out = []
    if prev.empty:
        out.append(L("Lado esquerdo sem barreiras: nada impede que as causas desencadeiem o evento.", "Left side without barriers: nothing stops causes from triggering the event."))
    if mit.empty:
        out.append(L("Lado direito sem barreiras: se o evento ocorrer, as consequências não são contidas.", "Right side without barriers: if the event occurs, consequences are not contained."))
    weak = lc[lc["conclusion"].isin(["ineffective", "partial", "not_tested"])] if not lc.empty else lc
    if not weak.empty:
        out.append(L(f"Barreiras fracas ou não testadas: {_ids(weak)}.", f"Weak or untested barriers: {_ids(weak)}."))
    if not out:
        out.append(L("Ambos os lados têm barreiras eficazes — mantenha os testes periódicos.", "Both sides have effective barriers — keep periodic testing."))
    return out
