"""Testes da estrutura do workflow. Não chamam nenhum modelo."""

from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from purchase_review.agent import root_agent


def test_raiz_e_sequencial_com_tres_etapas():
    assert isinstance(root_agent, SequentialAgent)
    nomes = [a.name for a in root_agent.sub_agents]
    assert nomes == ["intake", "analises_paralelas", "ciclo_de_revisao"]


def test_etapa_de_analises_roda_em_paralelo():
    paralelo = root_agent.sub_agents[1]
    assert isinstance(paralelo, ParallelAgent)
    assert {a.name for a in paralelo.sub_agents} == {"analista_fornecedor", "analista_preco"}


def test_ciclo_de_revisao_tem_limite_de_iteracoes():
    ciclo = root_agent.sub_agents[2]
    assert isinstance(ciclo, LoopAgent)
    assert ciclo.max_iterations == 3
    assert [a.name for a in ciclo.sub_agents] == ["redator", "revisor"]


def test_todo_agente_llm_grava_no_estado_da_sessao():
    def folhas(agente):
        for sub in getattr(agente, "sub_agents", []):
            yield from folhas(sub)
        if isinstance(agente, LlmAgent):
            yield agente

    llms = list(folhas(root_agent))
    assert len(llms) == 5
    assert all(a.output_key for a in llms)


def test_runner_e_construido_com_o_agente_raiz():
    runner = Runner(
        agent=root_agent,
        app_name="purchase_review",
        session_service=InMemorySessionService(),
    )
    assert runner.agent is root_agent
