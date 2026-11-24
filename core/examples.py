"""Industry example projects (PT content). Each one deliberately contains a few
gaps — a risk without controls, an orphan control, untested controls — so the
coverage analysis (ControlKit logic) has something to show."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from core.model import coerce_df, default_appetite, default_maturity, default_meta, new_project

T = dt.date.today()


def _d(days: int) -> str:
    return (T + dt.timedelta(days=days)).isoformat()


R_KEYS = ["type", "category", "title", "cause", "event", "effect", "owner", "p_inh", "i_inh", "velocity", "proximity",
          "strategy", "status", "trend", "p_tgt", "i_tgt", "prob_pct", "imp_min", "imp_ml", "imp_max"]
C_KEYS = ["name", "objective", "description", "risk_ids", "control_type", "nature", "frequency", "line", "owner",
          "evidence", "design_test", "operating_test", "test_date", "cost"]
A_KEYS = ["risk_id", "control_id", "description", "strategy", "owner", "start", "due", "cost", "status", "progress"]
K_KEYS = ["risk_id", "name", "unit", "direction", "amber", "red", "previous", "current", "frequency", "owner"]
F_KEYS = ["process", "failure_mode", "effect", "cause", "current_controls", "s", "o", "d", "action", "owner"]
S_KEYS = ["scenario", "asset", "threat", "tef_min", "tef_ml", "tef_max", "vuln_min", "vuln_ml", "vuln_max",
          "plm_min", "plm_ml", "plm_max", "slef", "slm_min", "slm_ml", "slm_max"]

A = lambda rid, cid, desc, strat, own, s, dur, cost, stt, prog: (rid, cid, desc, strat, own, _d(s), _d(s + dur), cost, stt, prog)  # noqa: E731

EXAMPLES: dict[str, dict] = {}

# ============================================================== SEGUROS
EXAMPLES["insurance"] = {
    "meta": dict(name="Seguradora — Gestão de Sinistros Acidentes", organisation="Seguradora Exemplo, S.A.",
                 industry="insurance", scope="Direção de Sinistros (Servicing Acidentes de Trabalho e Pessoais)",
                 objectives="Reduzir o prazo médio de regularização para 30 dias; NPS ≥ 45; rácio de despesas de gestão ≤ 8%; zero coimas ASF",
                 appetite_statement="A seguradora tem apetite reduzido para riscos de conformidade e conduta, apetite moderado para riscos operacionais que não afetem o cliente e procura ativamente oportunidades de automação.",
                 risk_capacity=8_000_000, impact_thresholds=[25_000, 150_000, 750_000, 3_000_000, 15_000_000]),
    "risks": [
        ("threat", "operational", "Fraude em sinistros de acidentes de trabalho", "Controlos de triagem manuais; Pressão de volume; Colusão entre prestadores",
         "Pagamento de indemnizações fraudulentas", "Perdas financeiras diretas; Aumento do rácio de sinistralidade", "Diretor de Sinistros",
         4, 4, 3, "short", "reduce", "treating", "up", 2, 3, 45, 150_000, 600_000, 2_500_000),
        ("threat", "compliance", "Incumprimento de prazos regulamentares ASF", "Picos de participações; Falhas de alertas no sistema",
         "Regularização fora do prazo legal", "Coimas ASF; Reclamações; Dano reputacional", "Compliance Officer",
         3, 4, 3, "medium", "reduce", "treating", "stable", 2, 2, None, 50_000, 250_000, 1_000_000),
        ("threat", "cyber", "Ransomware no sistema core de sinistros", "Phishing; Sistemas legados sem patch; Backups não isolados",
         "Indisponibilidade e cifragem do sistema de gestão de sinistros", "Paragem operacional; Fuga de dados de saúde (RGPD); Custos de recuperação", "CISO",
         3, 5, 5, "short", "reduce", "treating", "up", 2, 4, 15, 500_000, 2_000_000, 9_000_000),
        ("threat", "people", "Perda de gestores de sinistros experientes", "Mercado de trabalho competitivo; Carga de trabalho elevada",
         "Saída de colaboradores-chave", "Perda de conhecimento técnico; Aumento de prazos e erros", "Diretor de RH",
         3, 3, 2, "medium", "reduce", "open", "up", 2, 2, None, 40_000, 150_000, 400_000),
        ("threat", "reputational", "Reclamações públicas por mau serviço ao sinistrado", "Comunicação deficiente; Prazos longos",
         "Viralização de reclamações em redes sociais / Portal da Queixa", "Perda de clientes; Queda do NPS", "Diretor de Marketing",
         3, 3, 4, "short", "reduce", "monitoring", "stable", 2, 2, None, 30_000, 120_000, 600_000),
        ("threat", "supply_chain", "Dependência de rede de clínicas convencionadas", "Concentração em poucos prestadores; Contratos sem SLA",
         "Falha ou saída de prestador clínico relevante", "Atrasos no tratamento; Custos acrescidos", "Gestor de Prestadores",
         2, 4, 2, "long", "transfer", "open", "stable", 2, 3, None, 80_000, 300_000, 1_200_000),
        ("threat", "financial", "Subprovisionamento de reservas de sinistros", "Pressupostos atuariais desatualizados; Inflação médica",
         "Reservas técnicas insuficientes", "Impacto em resultados e solvência (SII)", "Atuário Responsável",
         2, 5, 2, "long", "reduce", "monitoring", "stable", 1, 5, None, 500_000, 2_500_000, 12_000_000),
        ("opportunity", "strategic", "Automação da triagem com IA (FNOL inteligente)", "Maturidade de modelos de IA; Dados históricos disponíveis",
         "Redução do prazo de regularização e deteção precoce de fraude", "Poupança de custos; Melhor experiência do cliente", "Diretor de Transformação",
         3, 4, 3, "medium", "exploit", "open", "stable", 4, 4, 40, 200_000, 600_000, 1_500_000),
        ("opportunity", "esg", "Programa de regresso ao trabalho e prevenção", "Parcerias com empregadores",
         "Menos dias de incapacidade temporária", "Redução de custos de sinistros; Ganho reputacional", "Diretor de Sinistros",
         2, 3, 2, "long", "enhance", "open", "stable", 3, 3, None, 50_000, 180_000, 450_000),
    ],
    "controls": [
        ("Scoring de fraude automático na participação", "Detetar sinistros suspeitos antes do pagamento", "Regras + modelo preditivo assinalam participações com score > 70 para a unidade antifraude",
         "R01", "detective", "automated", "continuous", "first", "Unidade Antifraude", "Log de alertas e decisões no sistema", "effective", "partial", _d(-60), 60_000),
        ("Dupla validação de pagamentos > 10 k€", "Evitar pagamentos indevidos de montante elevado", "Pagamentos acima do limiar exigem aprovação de segundo gestor",
         "R01", "preventive", "itdm", "continuous", "first", "Coordenador de Sinistros", "Workflow de aprovação com registo", "effective", "effective", _d(-45), 15_000),
        ("Alertas de prazos regulamentares no workflow", "Garantir cumprimento dos prazos ASF", "Sistema gera alertas a 5 e 2 dias do prazo legal com escalonamento automático",
         "R02", "preventive", "automated", "continuous", "first", "Gestor de Operações", "Relatório diário de prazos", "effective", "partial", _d(-30), 10_000),
        ("Revisão mensal de compliance de prazos", "Monitorizar a conformidade de prazos", "Amostragem de 50 processos/mês pela 2.ª linha",
         "R02", "detective", "manual", "monthly", "second", "Compliance Officer", "Relatório de amostragem assinado", "effective", "not_tested", None, 8_000),
        ("Backups imutáveis e testes de restauro", "Garantir recuperação após ataque", "Backups offline/imutáveis com teste de restauro trimestral",
         "R03", "corrective", "automated", "quarterly", "first", "Diretor de TI", "Relatórios de teste de restauro", "effective", "effective", _d(-20), 45_000),
        ("EDR e gestão de vulnerabilidades", "Prevenir intrusão e execução de malware", "EDR em todos os endpoints e patching crítico em 15 dias",
         "R03", "preventive", "automated", "continuous", "first", "CISO", "Dashboard de cobertura EDR e SLA de patching", "partial", "partial", _d(-15), 120_000),
        ("Formação anti-phishing com simulações", "Reduzir cliques em phishing", "Simulações mensais e formação obrigatória",
         "R03", "directive", "manual", "monthly", "first", "CISO", "Taxa de cliques por campanha", "effective", "not_tested", None, 12_000),
        ("Plano de sucessão e retenção de talento", "Reter competências críticas", "Mapeamento de posições críticas, planos de carreira e bónus de retenção",
         "R04", "preventive", "manual", "annual", "first", "Diretor de RH", "Plano aprovado pela Comissão Executiva", "partial", "not_tested", None, 70_000),
        ("Revisão atuarial independente das reservas", "Assegurar adequação das reservas", "Validação semestral pela função atuarial e auditor externo",
         "R07", "detective", "manual", "quarterly", "second", "Função Atuarial", "Relatório da função atuarial", "effective", "effective", _d(-90), 40_000),
        ("Política de gestão documental legada", "Controlo sem risco associado", "Revisão anual da política de arquivo físico",
         "", "directive", "manual", "annual", "first", "Serviços Gerais", "", "not_tested", "not_tested", None, 3_000),
    ],
    "actions": [
        A("R01", "C01", "Retreinar modelo de fraude com dados 2025–2026 e afinar limiares", "reduce", "Unidade Antifraude", -40, 90, 35_000, "in_progress", 50),
        A("R03", "C06", "Fechar lacunas de cobertura EDR em servidores legados", "reduce", "CISO", -10, 60, 25_000, "in_progress", 30),
        A("R05", "", "Implementar comunicação proativa por SMS em cada etapa do sinistro", "reduce", "Diretor de Marketing", 10, 75, 18_000, "not_started", 0),
        A("R06", "", "Renegociar contratos com SLA e penalizações; qualificar 2.º prestador por região", "transfer", "Gestor de Prestadores", -60, 45, 5_000, "in_progress", 40),
        A("R08", "", "Piloto de triagem FNOL com IA generativa em 2 linhas de negócio", "exploit", "Diretor de Transformação", 20, 120, 150_000, "not_started", 0),
        A("R02", "C04", "Executar teste de eficácia operacional à revisão de prazos", "reduce", "Auditoria Interna", -70, 30, 0, "in_progress", 60),
    ],
    "kris": [
        ("R01", "% sinistros com alerta de fraude confirmado", "%", "higher_worse", 3, 5, 3.2, 4.1, "monthly", "Unidade Antifraude"),
        ("R02", "% processos fora do prazo legal", "%", "higher_worse", 2, 4, 2.4, 1.8, "monthly", "Compliance Officer"),
        ("R03", "Vulnerabilidades críticas por corrigir > 15 dias", "n.º", "higher_worse", 5, 12, 9, 14, "weekly", "CISO"),
        ("R04", "Rotação voluntária de gestores (12 m)", "%", "higher_worse", 10, 15, 11, 12.5, "quarterly", "Diretor de RH"),
        ("R05", "NPS do processo de sinistro", "pts", "lower_worse", 40, 30, 38, 41, "monthly", "Diretor de Marketing"),
    ],
    "fmea": [
        ("Participação (FNOL)", "Dados de participação incompletos", "Atraso na abertura do processo", "Formulário sem validações", "Revisão manual", 5, 7, 5, "Validações obrigatórias no portal", "Gestor de Operações"),
        ("Peritagem", "Relatório de perito fora de prazo", "Incumprimento de prazo ASF", "Falta de peritos em picos", "Alerta manual", 7, 5, 6, "Bolsa de peritos externos com SLA", "Coordenador de Sinistros"),
        ("Pagamento", "IBAN incorreto ou fraudulento", "Pagamento indevido", "Alteração de IBAN sem validação", "Validação por chamada", 9, 3, 4, "Validação automática IBAN + confirmação 2FA", "Tesouraria"),
    ],
    "fair": [
        ("Ransomware no core de sinistros", "Sistema de gestão de sinistros", "Grupo cibercriminoso", 1, 3, 8, 0.05, 0.12, 0.30,
         150_000, 600_000, 3_000_000, 0.5, 100_000, 800_000, 5_000_000),
        ("Fuga de dados de saúde de sinistrados", "Base de dados clínica", "Insider / erro humano", 0.5, 2, 5, 0.10, 0.25, 0.50,
         20_000, 120_000, 600_000, 0.6, 50_000, 300_000, 2_000_000),
    ],
    "maturity": {"leadership": (3, 4), "governance": (3, 4), "strategy": (2, 4), "appetite": (2, 4), "process": (3, 4),
                 "controls": (3, 5), "quant": (2, 4), "kri": (2, 4), "culture": (2, 4), "reporting": (3, 4),
                 "resilience": (3, 4), "improvement": (2, 4)},
}

# ================================================================ BANCA
EXAMPLES["banking"] = {
    "meta": dict(name="Banco — Risco Operacional e de Conformidade", organisation="Banco Exemplo", industry="banking",
                 scope="Banca de retalho e meios de pagamento", objectives="Crescimento do crédito à habitação de 8%; Cost-to-income < 50%; Rácio CET1 > 13%",
                 appetite_statement="Tolerância zero para branqueamento de capitais e incumprimento de sanções; apetite moderado para risco de crédito dentro dos limites aprovados.",
                 risk_capacity=40_000_000, impact_thresholds=[100_000, 1_000_000, 5_000_000, 20_000_000, 100_000_000]),
    "risks": [
        ("threat", "compliance", "Falha na deteção de branqueamento de capitais (AML)", "Regras de monitorização desatualizadas; Volume de alertas falsos", "Transações suspeitas não reportadas", "Sanções do Banco de Portugal; Dano reputacional grave", "Head of Compliance", 3, 5, 3, "short", "reduce", "treating", "up", 2, 4, 10, 1_000_000, 8_000_000, 60_000_000),
        ("threat", "cyber", "Fraude em pagamentos digitais (APP fraud)", "Engenharia social; Pagamentos instantâneos", "Clientes induzidos a transferir para fraudadores", "Reembolsos; Reclamações; Regulação PSR", "Head of Fraud", 4, 3, 5, "short", "reduce", "treating", "up", 3, 2, 70, 400_000, 1_500_000, 4_000_000),
        ("threat", "financial", "Aumento do incumprimento no crédito ao consumo", "Subida de juros; Desemprego", "Aumento de NPL", "Imparidades; Redução de margem", "CRO", 3, 4, 2, "medium", "reduce", "monitoring", "up", 3, 3, 30, 2_000_000, 8_000_000, 25_000_000),
        ("threat", "operational", "Indisponibilidade do homebanking / app", "Dependência de cloud única; Alterações mal testadas", "Falha de serviço > 4 h", "Reclamações; Incumprimento DORA", "CIO", 3, 4, 5, "short", "reduce", "treating", "stable", 2, 3, None, 200_000, 1_500_000, 6_000_000),
        ("threat", "supply_chain", "Risco de terceiros críticos TIC (DORA)", "Concentração em fornecedores cloud; Contratos sem cláusulas DORA", "Falha de fornecedor crítico", "Interrupção de serviços; Sanções", "Head of Vendor Mgmt", 2, 4, 3, "medium", "reduce", "open", "stable", 2, 3, None, 300_000, 2_000_000, 10_000_000),
        ("threat", "esg", "Risco climático na carteira hipotecária", "Exposição a zonas de cheias; Transição energética", "Desvalorização de colaterais", "Imparidades; Exigências BCE", "CRO", 2, 3, 1, "long", "accept", "monitoring", "stable", 2, 3, None, 500_000, 2_000_000, 8_000_000),
        ("threat", "people", "Má conduta na comercialização de produtos", "Incentivos comerciais desalinhados", "Venda inadequada (mis-selling)", "Indemnizações; Coimas", "Head of Conduct", 2, 4, 2, "medium", "reduce", "open", "stable", 1, 4, None, 200_000, 1_000_000, 5_000_000),
        ("opportunity", "strategic", "Open banking e novos serviços de dados", "PSD3; Parcerias fintech", "Novas receitas de serviços", "Receitas adicionais; Retenção", "Head of Digital", 3, 4, 3, "medium", "exploit", "open", "stable", 4, 4, 35, 500_000, 2_000_000, 6_000_000),
    ],
    "controls": [
        ("Monitorização transacional AML baseada em cenários", "Detetar padrões de branqueamento", "Motor de regras + ML com afinação semestral", "R01", "detective", "automated", "continuous", "second", "Compliance", "Relatórios de afinação e alertas", "partial", "partial", _d(-50), 400_000),
        ("KYC reforçado e revisão periódica", "Conhecer o cliente e o seu risco", "Due diligence reforçada para PEP e alto risco", "R01, R07", "preventive", "itdm", "continuous", "first", "Rede Comercial", "Ficheiros KYC", "effective", "partial", _d(-40), 250_000),
        ("Confirmation of Payee e alertas de fraude em tempo real", "Prevenir transferências para fraudadores", "Validação nome/IBAN e scoring comportamental", "R02", "preventive", "automated", "continuous", "first", "Head of Fraud", "Logs do motor antifraude", "effective", "effective", _d(-25), 300_000),
        ("Stress tests de crédito trimestrais", "Antecipar deterioração da carteira", "Cenários macro adversos e limites de concentração", "R03", "detective", "manual", "quarterly", "second", "Risk Management", "Relatório ao ALCO", "effective", "effective", _d(-35), 60_000),
        ("Arquitetura ativa-ativa e testes de resiliência", "Garantir continuidade dos canais digitais", "Failover entre regiões e testes semestrais", "R04", "corrective", "automated", "quarterly", "first", "CIO", "Relatório de teste de failover", "effective", "partial", _d(-80), 500_000),
        ("Gestão de alterações (CAB)", "Evitar falhas por alterações", "Aprovação e testes obrigatórios antes de produção", "R04", "preventive", "itdm", "weekly", "first", "CIO", "Atas do CAB", "partial", "not_tested", None, 40_000),
        ("Registo de informação de terceiros TIC (DORA)", "Mapear dependências críticas", "Registo e avaliação anual de fornecedores", "R05", "detective", "manual", "annual", "second", "Vendor Mgmt", "Registo de informação", "partial", "not_tested", None, 30_000),
    ],
    "actions": [
        A("R01", "C01", "Recalibrar cenários AML e reduzir falsos positivos com ML supervisionado", "reduce", "Compliance", -30, 120, 180_000, "in_progress", 35),
        A("R05", "C07", "Rever contratos críticos com cláusulas DORA e planos de saída", "reduce", "Vendor Mgmt", 0, 150, 60_000, "not_started", 0),
        A("R06", "", "Mapear exposição a cheias com dados geoespaciais", "accept", "CRO", -90, 60, 40_000, "in_progress", 70),
        A("R07", "", "Rever esquema de incentivos comerciais (MiFID/IDD)", "reduce", "Head of Conduct", -100, 60, 10_000, "in_progress", 50),
        A("R08", "", "Lançar API marketplace com 3 parceiros fintech", "exploit", "Head of Digital", 15, 180, 350_000, "not_started", 0),
    ],
    "kris": [
        ("R01", "Alertas AML pendentes > 30 dias", "n.º", "higher_worse", 50, 120, 80, 135, "weekly", "Compliance"),
        ("R02", "Perdas por fraude APP (mensal)", "k€", "higher_worse", 80, 150, 95, 110, "monthly", "Head of Fraud"),
        ("R03", "Rácio NPL consumo", "%", "higher_worse", 3.5, 5, 3.1, 3.6, "monthly", "CRO"),
        ("R04", "Disponibilidade app (mensal)", "%", "lower_worse", 99.9, 99.5, 99.95, 99.7, "monthly", "CIO"),
    ],
    "fair": [("Fraude APP em larga escala", "Canal de pagamentos", "Rede de fraude organizada", 20, 60, 150, 0.05, 0.1, 0.2, 2_000, 9_000, 40_000, 0.2, 1_000, 5_000, 30_000)],
}

# ================================================================ SAÚDE
EXAMPLES["health"] = {
    "meta": dict(name="Hospital — Segurança do Doente e Operações", organisation="Hospital Exemplo, EPE", industry="health",
                 scope="Bloco operatório, urgência e farmácia hospitalar", objectives="Zero eventos sentinela; Tempo de espera em urgência < 4 h; Cumprimento de orçamento",
                 appetite_statement="Apetite muito baixo para riscos de segurança do doente e conformidade clínica; apetite moderado para inovação em serviços.",
                 risk_capacity=6_000_000, impact_thresholds=[10_000, 75_000, 400_000, 1_500_000, 6_000_000]),
    "risks": [
        ("threat", "health_safety", "Erro de medicação na administração", "Prescrição manual; Medicamentos com nomes semelhantes", "Administração de medicamento/dose errada", "Dano ao doente; Litígio", "Diretor Clínico", 3, 5, 5, "short", "reduce", "treating", "stable", 2, 4, None, 20_000, 200_000, 1_500_000),
        ("threat", "health_safety", "Infeção associada aos cuidados de saúde", "Baixa adesão à higiene das mãos; Sobrelotação", "Surto de infeção hospitalar", "Morbilidade; Prolongamento de internamentos", "PPCIRA", 3, 4, 3, "short", "reduce", "treating", "up", 2, 3, None, 50_000, 300_000, 1_200_000),
        ("threat", "operational", "Sobrelotação da urgência", "Picos sazonais; Altas tardias", "Tempos de espera > 8 h", "Risco clínico; Reclamações", "Diretor da Urgência", 4, 3, 4, "short", "reduce", "treating", "up", 3, 3, None, 30_000, 120_000, 500_000),
        ("threat", "cyber", "Ciberataque ao processo clínico eletrónico", "Sistemas legados; Dispositivos médicos ligados", "Indisponibilidade do SClínico", "Adiamento de cirurgias; Fuga de dados", "Responsável de Segurança", 3, 5, 5, "short", "reduce", "open", "up", 2, 4, 12, 200_000, 1_000_000, 5_000_000),
        ("threat", "people", "Escassez de enfermeiros e médicos especialistas", "Emigração; Burnout", "Turnos sem dotação segura", "Encerramento de serviços; Erros", "Diretor de RH", 4, 4, 2, "medium", "reduce", "open", "up", 3, 3, None, 100_000, 500_000, 2_000_000),
        ("threat", "supply_chain", "Rutura de stock de medicamentos críticos", "Fornecedor único; Atrasos logísticos", "Indisponibilidade de fármaco crítico", "Adiamento de tratamentos", "Diretor de Farmácia", 2, 4, 4, "short", "reduce", "monitoring", "stable", 2, 3, None, 20_000, 150_000, 600_000),
        ("opportunity", "strategic", "Hospitalização domiciliária", "Tecnologia de monitorização remota", "Libertação de camas", "Redução de custos; Satisfação do doente", "Conselho de Administração", 3, 4, 2, "medium", "enhance", "open", "stable", 4, 4, None, 200_000, 600_000, 1_200_000),
    ],
    "controls": [
        ("Prescrição eletrónica com alertas de interação", "Prevenir erros de prescrição", "Sistema bloqueia doses fora de intervalo", "R01", "preventive", "automated", "continuous", "first", "Farmácia", "Logs de alertas", "effective", "effective", _d(-30), 50_000),
        ("Dupla verificação de medicamentos de alto risco", "Prevenir erros de administração", "Verificação independente por 2 enfermeiros", "R01", "preventive", "manual", "continuous", "first", "Enfermeiro Diretor", "Registo de dupla verificação", "effective", "partial", _d(-45), 0),
        ("Auditorias de higiene das mãos", "Garantir adesão às precauções básicas", "Observação mensal por serviço", "R02", "detective", "manual", "monthly", "second", "PPCIRA", "Relatórios de auditoria", "effective", "effective", _d(-15), 15_000),
        ("Protocolo de gestão de vagas e altas", "Libertar camas atempadamente", "Huddle diário de gestão de camas", "R03", "preventive", "manual", "daily", "first", "Gestão de Doentes", "Atas do huddle", "partial", "partial", _d(-20), 10_000),
        ("Plano de contingência em papel e backups", "Manter atividade clínica em caso de indisponibilidade", "Procedimentos em papel e backups offline testados", "R04", "corrective", "manual", "quarterly", "first", "Responsável de Segurança", "Relatório de simulacro", "partial", "not_tested", None, 25_000),
        ("Stock de segurança e fornecedor alternativo", "Evitar ruturas", "Stock mínimo de 30 dias e 2.º fornecedor qualificado", "R06", "preventive", "itdm", "weekly", "first", "Farmácia", "Relatório de stocks", "effective", "effective", _d(-10), 40_000),
    ],
    "actions": [
        A("R04", "", "Segmentar rede de dispositivos médicos e implementar MFA", "reduce", "Responsável de Segurança", -20, 120, 150_000, "in_progress", 25),
        A("R05", "", "Programa de retenção e bolsa de horas para enfermeiros", "reduce", "Diretor de RH", -60, 180, 300_000, "in_progress", 40),
        A("R03", "C04", "Implementar gestão de altas até às 11h com indicador diário", "reduce", "Gestão de Doentes", -10, 60, 5_000, "in_progress", 20),
        A("R07", "", "Alargar hospitalização domiciliária a 20 camas", "enhance", "Conselho de Administração", 30, 180, 400_000, "not_started", 0),
    ],
    "kris": [
        ("R01", "Erros de medicação notificados / 1000 doses", "n.º", "higher_worse", 1, 2, 0.8, 1.2, "monthly", "Farmácia"),
        ("R02", "Taxa de IACS", "%", "higher_worse", 5, 8, 6.1, 5.4, "quarterly", "PPCIRA"),
        ("R03", "Doentes com espera > 4 h na urgência", "%", "higher_worse", 20, 35, 28, 33, "weekly", "Diretor da Urgência"),
        ("R05", "Rácio enfermeiro/doente (noite)", "doentes", "higher_worse", 8, 10, 9, 9.5, "monthly", "Enfermeiro Diretor"),
    ],
    "fmea": [
        ("Administração de medicação", "Troca de doente", "Medicamento administrado ao doente errado", "Ausência de pulseira/leitura", "Identificação verbal", 10, 3, 6, "Leitura por código de barras na cabeceira", "Enfermeiro Diretor"),
        ("Bloco operatório", "Lateralidade errada", "Cirurgia no local errado", "Ausência de marcação", "Checklist OMS", 10, 2, 3, "Auditoria de cumprimento da checklist", "Diretor do Bloco"),
        ("Esterilização", "Ciclo de esterilização falhado", "Infeção do sítio cirúrgico", "Equipamento sem manutenção", "Indicadores químicos", 9, 3, 4, "Indicadores biológicos em todos os ciclos", "Central de Esterilização"),
        ("Urgência", "Triagem de Manchester incorreta", "Atraso no atendimento de doente grave", "Sobrecarga do triador", "Auditoria anual", 9, 4, 6, "Retriagem automática por tempo de espera", "Diretor da Urgência"),
    ],
}

# =========================================================== AERO MRO
EXAMPLES["aero_mro"] = {
    "meta": dict(name="MRO Aeronáutico — Manutenção de Aeronaves e Motores", organisation="MRO Exemplo, S.A.", industry="aero_mro",
                 scope="Manutenção de aeronaves, motores e estruturas", objectives="Entregas no prazo ≥ 95%; Zero findings de nível 1 EASA; EBITDA ≥ 12%",
                 appetite_statement="Tolerância zero para riscos de aeronavegabilidade e segurança de voo; apetite moderado para riscos comerciais em novos contratos.",
                 risk_capacity=10_000_000, impact_thresholds=[50_000, 250_000, 1_000_000, 5_000_000, 20_000_000]),
    "risks": [
        ("threat", "compliance", "Finding de nível 1 em auditoria EASA Part-145", "Registos de manutenção incompletos; Formação desatualizada", "Suspensão da certificação", "Perda de licença; Cancelamento de contratos", "Quality Manager", 2, 5, 3, "medium", "reduce", "treating", "stable", 1, 5, None, 1_000_000, 5_000_000, 20_000_000),
        ("threat", "supply_chain", "Atraso na entrega de peças e motores (OEM)", "Constrangimentos globais de supply chain", "Peças críticas indisponíveis", "Aeronaves imobilizadas (AOG); Penalizações", "Supply Chain Director", 4, 4, 3, "short", "reduce", "treating", "up", 3, 3, 60, 200_000, 800_000, 3_000_000),
        ("threat", "health_safety", "Dano por objeto estranho (FOD)", "Ferramentas não controladas; Limpeza deficiente", "FOD em motor", "Dano de motor; Risco de segurança", "Safety Manager", 2, 5, 5, "short", "reduce", "monitoring", "stable", 1, 5, None, 100_000, 1_000_000, 8_000_000),
        ("threat", "people", "Falta de técnicos certificados B1/B2", "Envelhecimento da força de trabalho", "Capacidade insuficiente", "Atrasos de entrega", "Diretor de RH", 4, 3, 2, "medium", "reduce", "open", "up", 3, 2, None, 150_000, 500_000, 1_500_000),
        ("threat", "financial", "Derrapagem de custos em contratos de preço fixo", "Estimativas de horas otimistas; Achados não planeados", "Margem negativa no contrato", "Perdas financeiras", "Diretor Financeiro", 3, 4, 2, "medium", "reduce", "open", "stable", 2, 3, None, 200_000, 900_000, 3_000_000),
        ("threat", "cyber", "Espionagem industrial / dados de defesa", "Clientes militares; Phishing dirigido", "Exfiltração de dados técnicos", "Perda de contratos de defesa", "CISO", 2, 5, 4, "medium", "reduce", "open", "stable", 2, 4, None, 500_000, 2_000_000, 10_000_000),
        ("opportunity", "strategic", "Manutenção preditiva com digital twins", "Dados de sensores; Parcerias OEM", "Redução de TAT", "Diferenciação competitiva", "CTO", 3, 4, 2, "long", "exploit", "open", "stable", 4, 4, None, 300_000, 1_200_000, 3_000_000),
    ],
    "controls": [
        ("Auditorias internas de qualidade Part-145", "Detetar não conformidades antes da EASA", "Programa anual de auditorias por produto", "R01", "detective", "manual", "monthly", "second", "Quality", "Relatórios de auditoria e CAPA", "effective", "effective", _d(-40), 80_000),
        ("Gestão de competências e autorizações", "Garantir técnicos qualificados", "Matriz de autorizações com validade controlada", "R01, R04", "preventive", "itdm", "monthly", "first", "Quality", "Base de dados de autorizações", "effective", "partial", _d(-60), 30_000),
        ("Controlo de ferramentas (tool shadowing)", "Prevenir FOD", "Shadow boards e contagem no fecho de cada tarefa", "R03", "preventive", "manual", "continuous", "first", "Safety", "Registos de contagem", "effective", "effective", _d(-12), 20_000),
        ("Contratos-quadro com pool de peças", "Assegurar disponibilidade de peças", "Acordos de pool e stock consignado", "R02", "preventive", "manual", "quarterly", "first", "Supply Chain", "Contratos", "partial", "not_tested", None, 150_000),
        ("Revisão de orçamentos por engenharia", "Estimativas realistas", "Validação de horas com dados históricos", "R05", "preventive", "manual", "adhoc", "first", "Engenharia", "Checklist de revisão", "partial", "partial", _d(-30), 10_000),
    ],
    "actions": [
        A("R02", "C04", "Qualificar fornecedores alternativos para 20 part numbers críticos", "reduce", "Supply Chain", -45, 120, 60_000, "in_progress", 35),
        A("R04", "", "Academia interna de técnicos B1/B2 com 30 formandos/ano", "reduce", "Diretor de RH", -120, 365, 450_000, "in_progress", 30),
        A("R06", "", "Implementar NIST 800-171 / CMMC nível 2", "reduce", "CISO", 0, 240, 300_000, "not_started", 0),
        A("R07", "", "Piloto de digital twin para motores CFM56", "exploit", "CTO", 30, 200, 250_000, "not_started", 0),
    ],
    "kris": [
        ("R02", "Dias médios de espera por peças críticas", "dias", "higher_worse", 10, 20, 14, 17, "weekly", "Supply Chain"),
        ("R03", "Incidentes FOD", "n.º/mês", "higher_worse", 1, 3, 0, 1, "monthly", "Safety"),
        ("R04", "Taxa de ocupação de técnicos certificados", "%", "higher_worse", 90, 100, 93, 96, "monthly", "Produção"),
        ("R01", "Findings internos abertos > 60 dias", "n.º", "higher_worse", 3, 6, 5, 4, "monthly", "Quality"),
    ],
    "fmea": [
        ("Inspeção boroscópica", "Fissura não detetada", "Falha de motor em voo", "Fadiga do inspetor", "Inspeção dupla", 10, 2, 5, "Análise de imagem assistida por IA", "Engenharia"),
        ("Aperto de fixadores", "Binário incorreto", "Desprendimento de componente", "Chave não calibrada", "Calibração anual", 9, 3, 5, "Chaves digitais com registo", "Produção"),
        ("Registos", "Assinatura em falta no CRS", "Aeronave não aeronavegável", "Pressão de prazo", "Revisão de dossier", 8, 3, 3, "e-Logbook com bloqueio", "Quality"),
    ],
}

# ========================================================== TECH SAAS
EXAMPLES["tech_saas"] = {
    "meta": dict(name="SaaS B2B — Riscos Tecnológicos e de Negócio", organisation="CloudApp, Lda.", industry="tech_saas",
                 scope="Plataforma SaaS multi-tenant e operações", objectives="ARR + 40%; Disponibilidade 99,95%; Certificação ISO 27001; Churn < 8%",
                 appetite_statement="Apetite elevado para risco de inovação e crescimento; baixo para riscos de segurança da informação e privacidade.",
                 risk_capacity=3_000_000, impact_thresholds=[10_000, 60_000, 300_000, 1_000_000, 5_000_000]),
    "risks": [
        ("threat", "cyber", "Violação de dados de clientes", "Configurações cloud incorretas; Credenciais comprometidas", "Acesso não autorizado a dados multi-tenant", "Coimas RGPD; Perda de clientes", "CISO", 3, 5, 5, "short", "reduce", "treating", "up", 2, 4, 15, 100_000, 800_000, 4_000_000),
        ("threat", "operational", "Indisponibilidade prolongada da plataforma", "Deploys sem rollback; Dependência de uma região", "Downtime > 4 h", "Créditos de SLA; Churn", "CTO", 3, 4, 5, "short", "reduce", "treating", "stable", 2, 3, 30, 30_000, 150_000, 600_000),
        ("threat", "strategic", "Disrupção por concorrentes com IA generativa", "Ritmo de inovação do mercado", "Perda de diferenciação", "Queda do crescimento do ARR", "CEO", 4, 4, 3, "medium", "reduce", "open", "up", 3, 3, None, 200_000, 1_000_000, 3_000_000),
        ("threat", "people", "Dependência de engenheiros-chave", "Conhecimento não documentado", "Saída de engenheiro sénior", "Atraso no roadmap", "CTO", 3, 3, 3, "medium", "reduce", "open", "stable", 2, 2, None, 30_000, 120_000, 400_000),
        ("threat", "compliance", "Incumprimento do AI Act e RGPD", "Funcionalidades de IA sem avaliação de risco", "Uso não conforme de dados/IA", "Coimas e retirada de funcionalidades", "DPO", 2, 4, 2, "long", "reduce", "open", "up", 1, 4, None, 50_000, 400_000, 2_000_000),
        ("threat", "financial", "Concentração de receita em poucos clientes", "Top-3 clientes = 45% do ARR", "Perda de cliente-âncora", "Queda abrupta de receita", "CFO", 2, 5, 3, "medium", "reduce", "monitoring", "stable", 2, 4, None, 300_000, 900_000, 1_500_000),
        ("opportunity", "strategic", "Copiloto de IA integrado no produto", "Modelos fundacionais via API", "Upsell para plano premium", "Aumento do ARPU", "CPO", 4, 4, 3, "short", "exploit", "open", "stable", 5, 4, 60, 150_000, 500_000, 1_500_000),
    ],
    "controls": [
        ("MFA e acesso just-in-time", "Prevenir acesso indevido", "MFA obrigatório e privilégios temporários", "R01", "preventive", "automated", "continuous", "first", "Security", "Logs IdP", "effective", "effective", _d(-20), 25_000),
        ("CSPM — postura de segurança cloud", "Detetar configurações inseguras", "Scanner contínuo com alertas", "R01", "detective", "automated", "continuous", "first", "Security", "Dashboard CSPM", "effective", "partial", _d(-15), 30_000),
        ("Pentest anual e bug bounty", "Identificar vulnerabilidades", "Pentest externo e programa de recompensas", "R01", "detective", "manual", "annual", "third", "CISO", "Relatório de pentest", "effective", "effective", _d(-100), 40_000),
        ("Canary deploys com rollback automático", "Evitar falhas por deploy", "Deploy progressivo com métricas de saúde", "R02", "preventive", "automated", "continuous", "first", "SRE", "Pipeline CI/CD", "effective", "effective", _d(-10), 15_000),
        ("Plano de recuperação de desastres multi-região", "Recuperar em < 1 h", "Réplica noutra região e DR drill semestral", "R02", "corrective", "automated", "quarterly", "first", "SRE", "Relatório de DR drill", "partial", "not_tested", None, 60_000),
        ("Documentação e pair programming", "Reduzir dependência de pessoas", "ADRs e rotação de on-call", "R04", "preventive", "manual", "weekly", "first", "Engineering", "Wiki e ADRs", "partial", "partial", _d(-30), 5_000),
    ],
    "actions": [
        A("R03", "", "Roadmap de IA: 3 funcionalidades generativas em 2 trimestres", "reduce", "CPO", -30, 180, 250_000, "in_progress", 25),
        A("R05", "", "Avaliação de conformidade AI Act e DPIA das funcionalidades de IA", "reduce", "DPO", 0, 90, 30_000, "not_started", 0),
        A("R06", "", "Programa de diversificação de clientes mid-market", "reduce", "CFO", -60, 240, 120_000, "in_progress", 30),
        A("R02", "C05", "Executar DR drill multi-região e documentar RTO/RPO", "reduce", "SRE", -5, 30, 8_000, "in_progress", 10),
    ],
    "kris": [
        ("R01", "Findings críticos CSPM abertos", "n.º", "higher_worse", 3, 8, 6, 4, "weekly", "Security"),
        ("R02", "Disponibilidade (30 dias)", "%", "lower_worse", 99.95, 99.9, 99.97, 99.92, "monthly", "SRE"),
        ("R06", "Peso dos top-3 clientes no ARR", "%", "higher_worse", 35, 45, 47, 44, "quarterly", "CFO"),
        ("R04", "Bus factor (serviços com 1 só dono)", "n.º", "higher_worse", 2, 5, 6, 5, "quarterly", "Engineering"),
    ],
    "fair": [
        ("Credential stuffing na consola de clientes", "Portal de clientes", "Cibercriminosos", 5, 12, 30, 0.02, 0.05, 0.12, 5_000, 25_000, 150_000, 0.3, 20_000, 100_000, 800_000),
        ("Exposição de bucket S3 com dados de clientes", "Armazenamento cloud", "Erro interno", 0.2, 1, 3, 0.2, 0.4, 0.7, 30_000, 150_000, 900_000, 0.7, 50_000, 400_000, 3_000_000),
    ],
}

# ======================================================== CONSTRUCTION
EXAMPLES["construction"] = {
    "meta": dict(name="Projeto de Infraestrutura — Construção de Hospital", organisation="Construtora Exemplo, S.A.", industry="construction",
                 scope="Empreitada de construção (36 meses, 85 M€)", objectives="Concluir no prazo contratual; Custo ≤ orçamento + 5%; Zero acidentes graves",
                 appetite_statement="Apetite baixo para segurança em obra; apetite moderado para riscos de custo até à reserva de contingência (5%).",
                 risk_capacity=4_250_000, impact_thresholds=[50_000, 250_000, 1_000_000, 4_000_000, 15_000_000]),
    "risks": [
        ("threat", "project", "Condições geotécnicas imprevistas", "Prospeção insuficiente", "Necessidade de fundações especiais", "Atraso e sobrecusto", "Diretor de Obra", 3, 4, 3, "short", "reduce", "treating", "stable", 2, 3, 35, 300_000, 1_200_000, 4_000_000),
        ("threat", "financial", "Escalada de preços de materiais", "Inflação; Energia", "Aumento de custo de aço e betão", "Erosão da margem", "Diretor Financeiro", 4, 3, 2, "medium", "transfer", "treating", "up", 3, 2, 70, 300_000, 900_000, 2_500_000),
        ("threat", "health_safety", "Acidente grave em trabalhos em altura", "Proteções coletivas insuficientes", "Queda em altura", "Fatalidade; Paragem; Coimas ACT", "Coordenador de Segurança", 2, 5, 5, "short", "reduce", "treating", "stable", 1, 5, None, 100_000, 800_000, 5_000_000),
        ("threat", "supply_chain", "Atraso de subempreiteiro de AVAC", "Capacidade limitada; Falta de mão de obra", "Atraso no caminho crítico", "Penalizações contratuais", "Diretor de Obra", 3, 4, 2, "medium", "reduce", "open", "up", 2, 3, None, 200_000, 700_000, 2_000_000),
        ("threat", "compliance", "Atraso no licenciamento", "Pareceres de entidades externas", "Licenças emitidas tardiamente", "Paragem de frentes de obra", "Gestor de Licenciamento", 3, 3, 2, "short", "escalate", "open", "stable", 2, 3, None, 100_000, 400_000, 1_500_000),
        ("threat", "project", "Alterações de âmbito pelo dono de obra", "Requisitos clínicos em evolução", "Trabalhos a mais não orçamentados", "Disputas contratuais", "Gestor de Contrato", 4, 3, 2, "medium", "reduce", "open", "up", 3, 2, None, 150_000, 600_000, 2_000_000),
        ("opportunity", "project", "Pré-fabricação modular de quartos", "Fornecedor especializado disponível", "Redução do prazo de construção", "Poupança e bónus de conclusão antecipada", "Diretor de Obra", 3, 4, 2, "medium", "exploit", "open", "stable", 4, 4, 50, 200_000, 700_000, 1_500_000),
    ],
    "controls": [
        ("Campanha geotécnica complementar", "Reduzir incerteza do terreno", "Sondagens adicionais antes da fase de fundações", "R01", "preventive", "manual", "adhoc", "first", "Engenharia", "Relatório geotécnico", "effective", "effective", _d(-50), 120_000),
        ("Cláusula de revisão de preços", "Transferir risco de inflação", "Fórmula de revisão de preços no contrato", "R02", "corrective", "manual", "quarterly", "first", "Jurídico", "Contrato assinado", "effective", "effective", _d(-200), 0),
        ("Plano de Segurança e Saúde + inspeções diárias", "Prevenir acidentes", "Inspeções diárias, linhas de vida e formação", "R03", "preventive", "manual", "daily", "first", "Coord. Segurança", "Checklists diárias", "effective", "partial", _d(-7), 180_000),
        ("Monitorização semanal do caminho crítico (CPM)", "Detetar atrasos cedo", "Atualização do planeamento e Earned Value", "R04, R05", "detective", "itdm", "weekly", "first", "Planeamento", "Relatório semanal EVM", "effective", "effective", _d(-5), 30_000),
        ("Gestão formal de alterações (change control)", "Controlar alterações de âmbito", "Pedido de alteração com orçamento aprovado antes da execução", "R06", "preventive", "manual", "adhoc", "first", "Gestor de Contrato", "Registo de pedidos de alteração", "partial", "partial", _d(-25), 15_000),
    ],
    "actions": [
        A("R04", "", "Contratar subempreiteiro de AVAC alternativo em standby", "reduce", "Diretor de Obra", -15, 45, 40_000, "in_progress", 50),
        A("R05", "", "Reunião de escalonamento com a Câmara e entidades", "escalate", "Gestor de Licenciamento", -30, 20, 0, "done", 100),
        A("R07", "", "Estudo de viabilidade da pré-fabricação de 120 quartos", "exploit", "Diretor de Obra", 0, 60, 35_000, "not_started", 0),
        A("R03", "C03", "Auditoria externa de segurança trimestral", "reduce", "Coord. Segurança", -100, 60, 12_000, "in_progress", 70),
    ],
    "kris": [
        ("R04", "SPI (Schedule Performance Index)", "índice", "lower_worse", 0.95, 0.9, 0.97, 0.93, "weekly", "Planeamento"),
        ("R02", "CPI (Cost Performance Index)", "índice", "lower_worse", 0.97, 0.92, 0.98, 0.95, "monthly", "Diretor Financeiro"),
        ("R03", "Quase-acidentes reportados", "n.º/mês", "higher_worse", 8, 15, 6, 9, "monthly", "Coord. Segurança"),
        ("R06", "Pedidos de alteração pendentes", "n.º", "higher_worse", 5, 10, 7, 11, "weekly", "Gestor de Contrato"),
    ],
}

# ============================================================== RETAIL
EXAMPLES["retail"] = {
    "meta": dict(name="Retalho Alimentar — Cadeia de Abastecimento e Loja", organisation="Retalho Exemplo, S.A.", industry="retail",
                 scope="Centros de distribuição, lojas e e-commerce", objectives="Vendas comparáveis +4%; Ruturas < 3%; Desperdício alimentar -20%",
                 appetite_statement="Apetite moderado para riscos comerciais; baixo para segurança alimentar e conformidade.",
                 risk_capacity=12_000_000, impact_thresholds=[25_000, 150_000, 750_000, 3_000_000, 12_000_000]),
    "risks": [
        ("threat", "supply_chain", "Rutura de abastecimento de frescos", "Eventos climáticos; Greves de transporte", "Falta de produto em loja", "Perda de vendas; Insatisfação", "Diretor de Supply Chain", 3, 3, 4, "short", "reduce", "treating", "up", 2, 3, None, 100_000, 400_000, 1_500_000),
        ("threat", "health_safety", "Incidente de segurança alimentar", "Quebra da cadeia de frio", "Recolha de produto / intoxicação", "Dano à saúde; Coimas ASAE; Reputação", "Diretor de Qualidade", 2, 5, 5, "short", "reduce", "monitoring", "stable", 1, 5, None, 200_000, 1_000_000, 8_000_000),
        ("threat", "cyber", "Comprometimento de dados de cartões (PCI-DSS)", "POS vulneráveis", "Exfiltração de dados de pagamento", "Coimas e custos de reemissão", "CISO", 2, 4, 5, "medium", "reduce", "open", "stable", 1, 4, None, 200_000, 900_000, 4_000_000),
        ("threat", "operational", "Quebras e furtos em loja", "Self-checkout; Organização criminosa", "Aumento da quebra desconhecida", "Erosão da margem", "Diretor de Prevenção de Perdas", 4, 3, 2, "short", "reduce", "treating", "up", 3, 2, 85, 300_000, 900_000, 2_000_000),
        ("threat", "esg", "Não cumprimento de metas de desperdício e embalagem", "Legislação UE de embalagens", "Metas legais não atingidas", "Coimas; Reputação", "Diretor de Sustentabilidade", 3, 3, 1, "long", "reduce", "open", "stable", 2, 2, None, 100_000, 400_000, 1_200_000),
        ("opportunity", "strategic", "Retail media e dados de cliente", "Base de cartão de cliente com 3 M de membros", "Nova linha de receita publicitária", "Receita de alta margem", "Diretor Comercial", 3, 4, 3, "medium", "exploit", "open", "stable", 4, 4, 50, 500_000, 1_500_000, 4_000_000),
    ],
    "controls": [
        ("Monitorização IoT da temperatura", "Garantir cadeia de frio", "Sensores com alertas 24/7", "R02", "detective", "automated", "continuous", "first", "Qualidade", "Logs de temperatura", "effective", "effective", _d(-14), 90_000),
        ("Plano HACCP e auditorias de loja", "Prevenir contaminação", "Auditorias mensais HACCP", "R02", "preventive", "manual", "monthly", "second", "Qualidade", "Relatórios de auditoria", "effective", "effective", _d(-20), 60_000),
        ("Multi-sourcing de fornecedores de frescos", "Reduzir dependência", "≥2 fornecedores por categoria crítica", "R01", "preventive", "manual", "quarterly", "first", "Compras", "Matriz de fornecedores", "partial", "partial", _d(-60), 20_000),
        ("Segmentação de rede e tokenização PCI", "Proteger dados de cartão", "Tokenização ponto-a-ponto", "R03", "preventive", "automated", "continuous", "first", "CISO", "Relatório QSA", "effective", "not_tested", None, 150_000),
        ("Videovigilância com analítica", "Detetar furtos", "Câmaras com IA no self-checkout", "R04", "detective", "automated", "continuous", "first", "Prevenção de Perdas", "Relatórios de incidentes", "partial", "partial", _d(-30), 200_000),
    ],
    "actions": [
        A("R05", "", "Plano de redução de desperdício com doação e preços dinâmicos", "reduce", "Diretor de Sustentabilidade", -20, 180, 80_000, "in_progress", 20),
        A("R06", "", "Lançar plataforma de retail media com 10 marcas", "exploit", "Diretor Comercial", 10, 150, 300_000, "not_started", 0),
        A("R03", "C04", "Auditoria PCI-DSS 4.0 por QSA", "reduce", "CISO", 0, 60, 45_000, "not_started", 0),
    ],
    "kris": [
        ("R01", "Taxa de rutura em frescos", "%", "higher_worse", 3, 5, 2.8, 3.6, "weekly", "Supply Chain"),
        ("R04", "Quebra desconhecida (% vendas)", "%", "higher_worse", 1.2, 1.6, 1.3, 1.5, "monthly", "Prevenção de Perdas"),
        ("R02", "Alarmes de temperatura não resolvidos < 30 min", "n.º", "higher_worse", 3, 6, 2, 2, "weekly", "Qualidade"),
    ],
}

# ============================================================== PUBLIC
EXAMPLES["public"] = {
    "meta": dict(name="Instituição de Ensino Superior — Riscos Institucionais", organisation="Escola Superior Exemplo", industry="public",
                 scope="Atividades de ensino, investigação e serviços", objectives="Acreditação A3ES de todos os ciclos; Execução PRR ≥ 95%; Transição digital",
                 appetite_statement="Apetite baixo para riscos de conformidade e integridade; apetite moderado para inovação pedagógica.",
                 risk_capacity=1_500_000, impact_thresholds=[5_000, 30_000, 150_000, 600_000, 2_000_000]),
    "risks": [
        ("threat", "compliance", "Não acreditação de ciclo de estudos (A3ES)", "Corpo docente insuficientemente qualificado", "Decisão desfavorável da A3ES", "Encerramento do curso; Perda de receitas", "Presidente", 2, 5, 2, "long", "reduce", "treating", "stable", 1, 5, None, 150_000, 600_000, 2_000_000),
        ("threat", "financial", "Perda de financiamento PRR por baixa execução", "Procedimentos de contratação lentos", "Metas e marcos não cumpridos", "Devolução de verbas", "Administrador", 3, 4, 2, "short", "reduce", "treating", "up", 2, 3, 30, 100_000, 400_000, 1_500_000),
        ("threat", "cyber", "Ataque informático a plataformas de ensino", "Contas de estudantes comprometidas", "Indisponibilidade do Moodle/SIGA", "Interrupção letiva; Dados pessoais expostos", "Diretor de Sistemas", 3, 4, 5, "short", "reduce", "open", "up", 2, 3, None, 20_000, 120_000, 500_000),
        ("threat", "compliance", "Plágio e uso indevido de IA em avaliações", "Ferramentas generativas acessíveis", "Avaliações não fidedignas", "Perda de credibilidade dos diplomas", "Conselho Pedagógico", 4, 3, 3, "short", "reduce", "open", "up", 3, 2, None, 10_000, 50_000, 200_000),
        ("threat", "people", "Envelhecimento do corpo docente", "Restrições de contratação", "Aposentações sem substituição", "Perda de competências", "Presidente", 4, 3, 1, "long", "reduce", "open", "stable", 3, 2, None, 30_000, 120_000, 400_000),
        ("opportunity", "strategic", "Microcredenciais e formação ao longo da vida", "Procura de requalificação", "Novos públicos adultos", "Receitas próprias; Impacto social", "Vice-Presidente", 3, 3, 2, "medium", "exploit", "open", "stable", 4, 4, None, 50_000, 200_000, 600_000),
    ],
    "controls": [
        ("Sistema interno de garantia da qualidade", "Assegurar requisitos de acreditação", "Relatórios de autoavaliação e indicadores anuais", "R01", "detective", "manual", "annual", "second", "Gabinete de Qualidade", "Relatórios SIGQ", "effective", "effective", _d(-120), 25_000),
        ("Plano de qualificação docente", "Aumentar doutorados e especialistas", "Bolsas e dispensa de serviço", "R01, R05", "preventive", "manual", "annual", "first", "Presidente", "Plano aprovado", "partial", "not_tested", None, 60_000),
        ("Monitorização mensal de marcos PRR", "Detetar desvios de execução", "Painel de execução física e financeira", "R02", "detective", "itdm", "monthly", "first", "Administrador", "Painel PRR", "effective", "partial", _d(-15), 5_000),
        ("Código de integridade académica e deteção de plágio", "Prevenir fraude académica", "Software antiplágio e orientações sobre IA", "R04", "detective", "automated", "adhoc", "first", "Conselho Pedagógico", "Relatórios de similaridade", "partial", "partial", _d(-40), 12_000),
    ],
    "actions": [
        A("R03", "", "Implementar MFA para estudantes e docentes", "reduce", "Diretor de Sistemas", -10, 90, 25_000, "in_progress", 30),
        A("R04", "C04", "Redesenhar avaliações com componentes orais e projetos", "reduce", "Conselho Pedagógico", 0, 180, 5_000, "not_started", 0),
        A("R06", "", "Lançar 5 microcredenciais em parceria com empresas", "exploit", "Vice-Presidente", 30, 150, 40_000, "not_started", 0),
    ],
    "kris": [
        ("R02", "Taxa de execução financeira PRR", "%", "lower_worse", 80, 65, 72, 76, "monthly", "Administrador"),
        ("R01", "% docentes doutorados", "%", "lower_worse", 60, 50, 57, 58, "annual", "Presidente"),
        ("R03", "Contas comprometidas detetadas", "n.º/mês", "higher_worse", 5, 15, 9, 12, "monthly", "Diretor de Sistemas"),
    ],
}


def load_example(key: str) -> dict:
    ex = EXAMPLES[key]
    p = new_project()
    meta = default_meta()
    meta.update(ex["meta"])
    meta["assessor"] = "Risk Studio (exemplo)"
    p["meta"] = meta
    p["risks"] = coerce_df("risks", pd.DataFrame([dict(zip(R_KEYS, r)) for r in ex["risks"]]))
    p["controls"] = coerce_df("controls", pd.DataFrame([dict(zip(C_KEYS, c)) for c in ex["controls"]]))
    p["actions"] = coerce_df("actions", pd.DataFrame([dict(zip(A_KEYS, a)) for a in ex.get("actions", [])]))
    p["kris"] = coerce_df("kris", pd.DataFrame([dict(zip(K_KEYS, k)) for k in ex.get("kris", [])]))
    p["fmea"] = coerce_df("fmea", pd.DataFrame([dict(zip(F_KEYS, f)) for f in ex.get("fmea", [])]))
    p["fair"] = coerce_df("fair", pd.DataFrame([dict(zip(S_KEYS, s)) for s in ex.get("fair", [])]))
    p["appetite"] = default_appetite()
    m = default_maturity()
    for dim, (cur, tgt) in ex.get("maturity", {}).items():
        m.loc[m["dim"] == dim, ["current", "target"]] = [cur, tgt]
    p["maturity"] = m
    return p
