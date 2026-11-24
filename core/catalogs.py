"""Controlled vocabularies, scales and reference parameters.

Values are stored internally as stable *codes* (e.g. "threat", "preventive");
labels are shown in the active language. Import accepts codes, PT or EN labels.
"""
from __future__ import annotations

from core.i18n import lang

# ---------------------------------------------------------------- catalogs
CATALOGS: dict[str, dict[str, tuple[str, str]]] = {
    "type": {
        "threat": ("Ameaça", "Threat"),
        "opportunity": ("Oportunidade", "Opportunity"),
    },
    "category": {
        "strategic": ("Estratégico", "Strategic"),
        "operational": ("Operacional", "Operational"),
        "financial": ("Financeiro", "Financial"),
        "compliance": ("Conformidade & Legal", "Compliance & Legal"),
        "cyber": ("Cibersegurança & TI", "Cyber & IT"),
        "reputational": ("Reputacional", "Reputational"),
        "esg": ("ESG & Clima", "ESG & Climate"),
        "supply_chain": ("Cadeia de abastecimento", "Supply chain"),
        "project": ("Projeto", "Project"),
        "people": ("Pessoas & Talento", "People & Talent"),
        "health_safety": ("Saúde & Segurança", "Health & Safety"),
    },
    "status": {
        "open": ("Aberto", "Open"),
        "treating": ("Em tratamento", "Being treated"),
        "monitoring": ("Em monitorização", "Monitoring"),
        "closed": ("Fechado", "Closed"),
    },
    "strategy": {
        "avoid": ("Evitar", "Avoid"),
        "reduce": ("Mitigar / Reduzir", "Mitigate / Reduce"),
        "transfer": ("Transferir", "Transfer"),
        "accept": ("Aceitar", "Accept"),
        "escalate": ("Escalar", "Escalate"),
        "exploit": ("Explorar", "Exploit"),
        "enhance": ("Potenciar", "Enhance"),
        "share": ("Partilhar", "Share"),
    },
    "trend": {
        "up": ("↑ A agravar", "↑ Worsening"),
        "stable": ("→ Estável", "→ Stable"),
        "down": ("↓ A melhorar", "↓ Improving"),
    },
    "proximity": {
        "short": ("< 6 meses", "< 6 months"),
        "medium": ("6–12 meses", "6–12 months"),
        "long": ("> 12 meses", "> 12 months"),
    },
    "control_type": {
        "preventive": ("Preventivo", "Preventive"),
        "detective": ("Detetivo", "Detective"),
        "corrective": ("Corretivo", "Corrective"),
        "directive": ("Diretivo", "Directive"),
    },
    "nature": {
        "automated": ("Automático", "Automated"),
        "itdm": ("Manual dependente de TI", "IT-dependent manual"),
        "manual": ("Manual", "Manual"),
    },
    "frequency": {
        "continuous": ("Contínuo", "Continuous"),
        "daily": ("Diário", "Daily"),
        "weekly": ("Semanal", "Weekly"),
        "monthly": ("Mensal", "Monthly"),
        "quarterly": ("Trimestral", "Quarterly"),
        "annual": ("Anual", "Annual"),
        "adhoc": ("Por evento", "Event-driven"),
    },
    "line": {
        "first": ("1.ª linha (gestão)", "1st line (management)"),
        "second": ("2.ª linha (risco/compliance)", "2nd line (risk/compliance)"),
        "third": ("3.ª linha (auditoria interna)", "3rd line (internal audit)"),
    },
    "test": {
        "effective": ("Eficaz", "Effective"),
        "partial": ("Parcialmente eficaz", "Partially effective"),
        "ineffective": ("Ineficaz", "Ineffective"),
        "not_tested": ("Não testado", "Not tested"),
    },
    "action_status": {
        "not_started": ("Não iniciada", "Not started"),
        "in_progress": ("Em curso", "In progress"),
        "done": ("Concluída", "Done"),
        "cancelled": ("Cancelada", "Cancelled"),
    },
    "direction": {
        "higher_worse": ("Maior = pior", "Higher = worse"),
        "lower_worse": ("Menor = pior", "Lower = worse"),
    },
}


def label(catalog: str, code) -> str:
    if code is None or (isinstance(code, float) and code != code):
        return ""
    item = CATALOGS.get(catalog, {}).get(str(code))
    if not item:
        return str(code)
    return item[1] if lang() == "en" else item[0]


def labels(catalog: str) -> list[str]:
    return [label(catalog, c) for c in CATALOGS[catalog]]


def code_from_any(catalog: str, value, default: str | None = None):
    """Map a code / PT label / EN label (case-insensitive) back to the code."""
    if value is None:
        return default
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        return default
    cat = CATALOGS.get(catalog, {})
    if s in cat:
        return s
    low = s.lower()
    for code, (pt, en) in cat.items():
        if low in (code.lower(), pt.lower(), en.lower()):
            return code
    # tolerant prefix match ("Mitigar" -> reduce)
    for code, (pt, en) in cat.items():
        if pt.lower().startswith(low) or en.lower().startswith(low):
            return code
    return default


# ------------------------------------------------------------------ scales
PROB_SCALE = {
    1: (("Rara", "Rare"), "< 5%", 0.03),
    2: (("Improvável", "Unlikely"), "5–20%", 0.12),
    3: (("Possível", "Possible"), "20–50%", 0.35),
    4: (("Provável", "Likely"), "50–80%", 0.65),
    5: (("Quase certa", "Almost certain"), "> 80%", 0.90),
}

IMPACT_SCALE = {
    1: ("Insignificante", "Insignificant"),
    2: ("Menor", "Minor"),
    3: ("Moderado", "Moderate"),
    4: ("Maior", "Major"),
    5: ("Catastrófico", "Catastrophic"),
}

# Qualitative impact descriptors (multi-dimensional impact table)
IMPACT_DESCRIPTORS = {
    "reputation": (("Reputação", "Reputation"), [
        ("Sem cobertura externa", "No external coverage"),
        ("Queixas locais isoladas", "Isolated local complaints"),
        ("Cobertura regional / redes sociais", "Regional / social media coverage"),
        ("Cobertura nacional negativa", "Negative national coverage"),
        ("Dano duradouro à marca", "Lasting brand damage"),
    ]),
    "people": (("Pessoas / Segurança", "People / Safety"), [
        ("Sem lesões", "No injury"),
        ("Primeiros socorros", "First aid"),
        ("Lesão com baixa", "Lost-time injury"),
        ("Lesão grave / incapacidade", "Serious injury / disability"),
        ("Fatalidade", "Fatality"),
    ]),
    "compliance": (("Conformidade", "Compliance"), [
        ("Incumprimento menor interno", "Minor internal breach"),
        ("Advertência do regulador", "Regulator warning"),
        ("Coima / auditoria regulatória", "Fine / regulatory audit"),
        ("Sanção relevante / processo", "Material sanction / litigation"),
        ("Perda de licença", "Loss of licence"),
    ]),
    "operations": (("Operações", "Operations"), [
        ("Interrupção < 1 h", "Disruption < 1 h"),
        ("Interrupção < 1 dia", "Disruption < 1 day"),
        ("Interrupção 1–3 dias", "Disruption 1–3 days"),
        ("Interrupção 1–2 semanas", "Disruption 1–2 weeks"),
        ("Interrupção > 2 semanas", "Disruption > 2 weeks"),
    ]),
}

DEFAULT_IMPACT_THRESHOLDS = [10_000, 100_000, 500_000, 2_000_000, 10_000_000]

LEVELS = [  # (min_score, max_score, code, PT, EN, colour)
    (1, 4, "low", "Baixo", "Low", "#22c55e"),
    (5, 9, "moderate", "Moderado", "Moderate", "#eab308"),
    (10, 14, "high", "Elevado", "High", "#f97316"),
    (15, 25, "critical", "Crítico", "Critical", "#ef4444"),
]
OPP_LEVELS = [
    (1, 4, "low", "Baixa", "Low", "#93c5fd"),
    (5, 9, "moderate", "Moderada", "Moderate", "#60a5fa"),
    (10, 14, "high", "Elevada", "High", "#3b82f6"),
    (15, 25, "critical", "Muito elevada", "Very high", "#1d4ed8"),
]

TEST_FACTOR = {"effective": 1.0, "partial": 0.5, "ineffective": 0.0, "not_tested": 0.3}
NATURE_STRENGTH = {"automated": 0.80, "itdm": 0.65, "manual": 0.55}
VELOCITY_FACTOR = {1: 0.8, 2: 0.9, 3: 1.0, 4: 1.1, 5: 1.2}
PROXIMITY_FACTOR = {"short": 1.1, "medium": 1.0, "long": 0.9}

DEFAULT_APPETITE = {  # category: (appetite, tolerance) on residual 1–25 score
    "strategic": (12, 15),
    "operational": (9, 12),
    "financial": (8, 12),
    "compliance": (4, 6),
    "cyber": (6, 9),
    "reputational": (6, 9),
    "esg": (8, 12),
    "supply_chain": (9, 12),
    "project": (10, 14),
    "people": (9, 12),
    "health_safety": (3, 5),
}

# ISO 31000 / COSO ERM maturity dimensions
MATURITY_DIMENSIONS = [
    ("leadership", "Liderança & compromisso", "Leadership & commitment"),
    ("governance", "Governação & Modelo das 3 Linhas", "Governance & Three Lines Model"),
    ("strategy", "Integração na estratégia e desempenho", "Integration with strategy & performance"),
    ("appetite", "Apetite e tolerância ao risco", "Risk appetite & tolerance"),
    ("process", "Processo (identificar, analisar, avaliar)", "Process (identify, analyse, evaluate)"),
    ("controls", "Controlos internos & testes", "Internal controls & testing"),
    ("quant", "Quantificação & dados", "Quantification & data"),
    ("kri", "Monitorização & KRIs", "Monitoring & KRIs"),
    ("culture", "Cultura de risco & competências", "Risk culture & skills"),
    ("reporting", "Reporte & comunicação", "Reporting & communication"),
    ("resilience", "Resiliência & continuidade", "Resilience & continuity"),
    ("improvement", "Melhoria contínua", "Continual improvement"),
]
MATURITY_LEVELS = {
    1: ("Inicial (ad hoc)", "Initial (ad hoc)"),
    2: ("Repetível", "Repeatable"),
    3: ("Definido", "Defined"),
    4: ("Gerido (medido)", "Managed (measured)"),
    5: ("Otimizado / integrado", "Optimised / integrated"),
}

INDUSTRIES = {
    "insurance": ("Seguros", "Insurance"),
    "banking": ("Banca", "Banking"),
    "health": ("Saúde (hospital)", "Healthcare (hospital)"),
    "aero_mro": ("Aeronáutica (MRO)", "Aerospace (MRO)"),
    "tech_saas": ("Tecnologia / SaaS", "Technology / SaaS"),
    "construction": ("Construção & Projetos", "Construction & Projects"),
    "retail": ("Retalho & Distribuição", "Retail & Distribution"),
    "public": ("Setor Público & Educação", "Public Sector & Education"),
    "other": ("Outra", "Other"),
}
