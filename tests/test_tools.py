from unittest.mock import MagicMock

from purchase_review.tools import (
    aprovar_recomendacao,
    consultar_historico_fornecedor,
    consultar_preco_referencia,
)


def test_fornecedor_encontrado_calcula_otif():
    r = consultar_historico_fornecedor("Alfa Parafusos")
    assert r["status"] == "success"
    assert r["otif_pct"] == 93.8  # 45 de 48 entregas no prazo
    assert r["nao_conformidades"] == 1


def test_fornecedor_busca_tolera_acento_e_caixa():
    r = consultar_historico_fornecedor("  BETA Polímeros ")
    assert r["status"] == "success"
    assert r["entregas_12m"] == 40


def test_fornecedor_inexistente():
    assert consultar_historico_fornecedor("Fornecedor X")["status"] == "not_found"


def test_preco_dentro_da_tolerancia():
    r = consultar_preco_referencia("Resina PP", 10.0)  # ref 9,80; tolerância 8%
    assert r["status"] == "success"
    assert r["desvio_pct"] == 2.0
    assert r["dentro_da_tolerancia"] is True


def test_preco_acima_da_tolerancia():
    r = consultar_preco_referencia("Resina PP", 11.0)
    assert r["desvio_pct"] == 12.2
    assert r["dentro_da_tolerancia"] is False


def test_preco_item_inexistente():
    assert consultar_preco_referencia("Item X", 1.0)["status"] == "not_found"


def test_aprovar_recomendacao_sinaliza_saida_do_loop():
    ctx = MagicMock()
    ctx.actions.escalate = False
    r = aprovar_recomendacao(ctx)
    assert ctx.actions.escalate is True
    assert r["status"] == "success"
