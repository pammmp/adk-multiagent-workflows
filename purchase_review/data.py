"""Dados FICTÍCIOS usados pelas ferramentas do exemplo.

Nenhum dado real de empresa ou cliente é usado neste repositório.
"""

FORNECEDORES = {
    "alfa parafusos": {
        "nome": "Alfa Parafusos (fictício)",
        "entregas_12m": 48,
        "entregas_no_prazo": 45,
        "nao_conformidades": 1,
    },
    "beta polimeros": {
        "nome": "Beta Polímeros (fictício)",
        "entregas_12m": 40,
        "entregas_no_prazo": 31,
        "nao_conformidades": 4,
    },
    "gama embalagens": {
        "nome": "Gama Embalagens (fictício)",
        "entregas_12m": 25,
        "entregas_no_prazo": 25,
        "nao_conformidades": 0,
    },
}

PRECOS_REFERENCIA = {
    "parafuso m8": {"preco_ref": 0.42, "unidade": "un", "tolerancia_pct": 10.0},
    "resina pp": {"preco_ref": 9.80, "unidade": "kg", "tolerancia_pct": 8.0},
    "caixa papelao 40x30": {"preco_ref": 3.10, "unidade": "un", "tolerancia_pct": 12.0},
}
