"""Teste de ponta a ponta com um modelo FALSO (sem chave de API e sem internet).

Prova que: o estado da sessão passa de um agente para o outro, as duas análises
rodam, as ferramentas são chamadas e o ciclo de revisão termina quando o revisor
chama aprovar_recomendacao. Não avalia a qualidade das respostas de um LLM real.
"""

import asyncio

from google.adk.agents import LlmAgent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from purchase_review.agent import root_agent


def _instrucao(llm_request) -> str:
    si = llm_request.config.system_instruction
    return si if isinstance(si, str) else str(si)


def _ja_tem_resposta_de_ferramenta(llm_request) -> bool:
    return any(
        getattr(p, "function_response", None)
        for c in llm_request.contents
        for p in (c.parts or [])
    )


def _texto(txt):
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=txt)]))


def _chamada(nome, args):
    part = types.Part(function_call=types.FunctionCall(name=nome, args=args))
    return LlmResponse(content=types.Content(role="model", parts=[part]))


class ModeloFalso(BaseLlm):
    model: str = "modelo-falso"

    async def generate_content_async(self, llm_request, stream=False):
        instr = _instrucao(llm_request)
        com_resposta = _ja_tem_resposta_de_ferramenta(llm_request)
        if "Extraia e responda" in instr:
            yield _texto(
                "item: Resina PP\nfornecedor: Beta Polímeros\n"
                "quantidade: 500\npreco_unitario_ofertado: 11.0"
            )
        elif "consultar_historico_fornecedor" in instr:
            yield _texto("OTIF 77,5% e 4 não conformidades: risco de entrega.") if com_resposta \
                else _chamada("consultar_historico_fornecedor", {"fornecedor": "Beta Polímeros"})
        elif "consultar_preco_referencia" in instr:
            yield _texto("Desvio de 12,2%, acima da tolerância.") if com_resposta \
                else _chamada("consultar_preco_referencia",
                              {"item": "Resina PP", "preco_unitario_ofertado": 11.0})
        elif "Escreva uma recomendação" in instr:
            yield _texto("Não aprovar: Beta Polímeros com OTIF 77,5% e preço 12,2% acima.")
        elif "Revise a recomendação" in instr:
            yield _texto("Aprovada.") if com_resposta else _chamada("aprovar_recomendacao", {})
        else:
            yield _texto("instrução inesperada")


def _trocar_modelo(agente, modelo):
    for sub in getattr(agente, "sub_agents", []):
        _trocar_modelo(sub, modelo)
    if isinstance(agente, LlmAgent):
        agente.model = modelo


async def _rodar(mensagem: str):
    _trocar_modelo(root_agent, ModeloFalso())
    sessoes = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name="teste", session_service=sessoes)
    sessao = await sessoes.create_session(app_name="teste", user_id="u")
    msg = types.Content(role="user", parts=[types.Part(text=mensagem)])
    autores = []
    async for evento in runner.run_async(user_id="u", session_id=sessao.id, new_message=msg):
        autores.append(evento.author)
    final = await sessoes.get_session(app_name="teste", user_id="u", session_id=sessao.id)
    return final.state, autores


def test_fluxo_completo_com_modelo_falso():
    estado, autores = asyncio.run(_rodar("Comprar 500 kg de resina PP da Beta a R$ 11,00"))

    assert "Resina PP" in estado["pedido_estruturado"]
    assert "OTIF" in estado["analise_fornecedor"]
    assert "Desvio" in estado["analise_preco"]
    assert estado["recomendacao"].startswith("Não aprovar")
    # o ciclo terminou na 1ª volta: o revisor aprovou, então o redator rodou uma vez só
    assert autores.count("redator") == 1
    assert autores.count("revisor") >= 1


def test_entrada_sensivel_nao_chega_ao_modelo():
    estado, autores = asyncio.run(_rodar("Comprar com o CPF 123.456.789-09"))
    assert "recomendacao" not in estado
    assert "intake" not in autores
