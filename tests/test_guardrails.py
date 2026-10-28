from types import SimpleNamespace
from unittest.mock import MagicMock

from google.genai import types

from purchase_review.guardrails import (
    MAX_CHAMADAS_FERRAMENTA,
    contem_dado_sensivel,
    limitar_chamadas_ferramenta,
    preparar_e_validar_entrada,
)


def _ctx(texto: str):
    conteudo = types.Content(role="user", parts=[types.Part(text=texto)])
    return SimpleNamespace(state={}, user_content=conteudo)


def test_detecta_cpf_e_cartao():
    assert contem_dado_sensivel("meu cpf é 123.456.789-09")
    assert contem_dado_sensivel("cartão 4111 1111 1111 1111")


def test_nao_marca_pedido_normal_como_sensivel():
    assert not contem_dado_sensivel("Comprar 500 kg de resina PP da Beta a R$ 10,20 o kg")
    assert not contem_dado_sensivel("Pedido 20260012, 1000 parafusos M8")


def test_entrada_normal_inicializa_estado_e_segue():
    ctx = _ctx("Comprar 1000 parafusos M8 da Alfa a R$ 0,45")
    assert preparar_e_validar_entrada(ctx) is None
    assert ctx.state["feedback_revisor"] == "(nenhum feedback ainda)"
    assert ctx.state["chamadas_ferramenta"] == 0


def test_entrada_sensivel_devolve_bloqueio():
    ctx = _ctx("Compra com CPF 123.456.789-09")
    resposta = preparar_e_validar_entrada(ctx)
    assert resposta is not None
    assert "dados pessoais" in resposta.parts[0].text


def test_limite_de_chamadas_de_ferramenta():
    ctx = SimpleNamespace(state={})
    tool = MagicMock()
    for _ in range(MAX_CHAMADAS_FERRAMENTA):
        assert limitar_chamadas_ferramenta(tool, {}, ctx) is None
    bloqueio = limitar_chamadas_ferramenta(tool, {}, ctx)
    assert bloqueio["status"] == "blocked"
