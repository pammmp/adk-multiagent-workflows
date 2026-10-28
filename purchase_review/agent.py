"""Workflow multiagente de revisão de solicitação de compra (exemplo com dados fictícios).

Fluxo:
    SequentialAgent
      1. intake                  extrai os campos do pedido
      2. analises_paralelas      ParallelAgent: fornecedor e preço ao mesmo tempo
      3. ciclo_de_revisao        LoopAgent: redator escreve, revisor critica, até aprovar

Os agentes se comunicam pelo estado da sessão (output_key -> {chave} nas instruções).
Cuidado: chaves {assim} nas instruções são lidas como variáveis de estado, então
não use chaves literais nos textos.
"""

import os

from google.adk.agents import LlmAgent, LoopAgent, ParallelAgent, SequentialAgent

from .guardrails import limitar_chamadas_ferramenta, preparar_e_validar_entrada
from .tools import aprovar_recomendacao, consultar_historico_fornecedor, consultar_preco_referencia

# Configurável por variável de ambiente. Confirme na documentação do ADK/Vertex
# quais modelos estão disponíveis para o seu projeto.
MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")

intake = LlmAgent(
    name="intake",
    model=MODEL,
    description="Extrai item, fornecedor, quantidade e preço unitário da solicitação.",
    instruction=(
        "Você recebe uma solicitação de compra em texto livre. Extraia e responda "
        "somente com quatro linhas, sem comentários: item, fornecedor, quantidade, "
        "preco_unitario_ofertado (número em reais). Se algum campo faltar, escreva "
        "'não informado' naquele campo."
    ),
    output_key="pedido_estruturado",
)

analista_fornecedor = LlmAgent(
    name="analista_fornecedor",
    model=MODEL,
    description="Avalia o histórico de entregas do fornecedor.",
    instruction=(
        "Pedido:\n{pedido_estruturado}\n\n"
        "Use a ferramenta consultar_historico_fornecedor com o fornecedor do pedido. "
        "Resuma em até 3 linhas o OTIF, as não conformidades e se há risco de entrega. "
        "Se a ferramenta não encontrar o fornecedor, diga isso claramente."
    ),
    tools=[consultar_historico_fornecedor],
    before_tool_callback=limitar_chamadas_ferramenta,
    output_key="analise_fornecedor",
)

analista_preco = LlmAgent(
    name="analista_preco",
    model=MODEL,
    description="Compara o preço ofertado com o preço de referência.",
    instruction=(
        "Pedido:\n{pedido_estruturado}\n\n"
        "Use a ferramenta consultar_preco_referencia com o item e o preço unitário "
        "ofertado. Resuma em até 3 linhas o desvio percentual e se está dentro da "
        "tolerância. Se a ferramenta não encontrar o item, diga isso claramente."
    ),
    tools=[consultar_preco_referencia],
    before_tool_callback=limitar_chamadas_ferramenta,
    output_key="analise_preco",
)

analises_paralelas = ParallelAgent(
    name="analises_paralelas",
    description="Roda as análises de fornecedor e de preço em paralelo.",
    sub_agents=[analista_fornecedor, analista_preco],
)

redator = LlmAgent(
    name="redator",
    model=MODEL,
    description="Escreve a recomendação de compra.",
    instruction=(
        "Escreva uma recomendação curta (máximo 6 linhas) com a decisão: aprovar, "
        "aprovar com ressalvas ou não aprovar. Cite o fornecedor, o desvio de preço "
        "e o OTIF.\n\n"
        "Pedido:\n{pedido_estruturado}\n\n"
        "Análise do fornecedor:\n{analise_fornecedor}\n\n"
        "Análise de preço:\n{analise_preco}\n\n"
        "Feedback do revisor (se houver, corrija a recomendação):\n{feedback_revisor}"
    ),
    output_key="recomendacao",
)

revisor = LlmAgent(
    name="revisor",
    model=MODEL,
    description="Revisa a recomendação e aprova ou devolve feedback.",
    instruction=(
        "Revise a recomendação abaixo. Ela está aprovada se tiver decisão clara, "
        "citar o fornecedor e citar o desvio de preço. Se estiver aprovada, chame a "
        "ferramenta aprovar_recomendacao. Se não estiver, responda apenas com um "
        "feedback objetivo de uma ou duas linhas dizendo o que falta.\n\n"
        "Recomendação:\n{recomendacao}"
    ),
    tools=[aprovar_recomendacao],
    before_tool_callback=limitar_chamadas_ferramenta,
    output_key="feedback_revisor",
)

ciclo_de_revisao = LoopAgent(
    name="ciclo_de_revisao",
    description="Repete redação e revisão até o revisor aprovar (máximo de 3 voltas).",
    sub_agents=[redator, revisor],
    max_iterations=3,
)

root_agent = SequentialAgent(
    name="revisao_solicitacao_compra",
    description="Revisa uma solicitação de compra: extrai, analisa em paralelo e recomenda.",
    sub_agents=[intake, analises_paralelas, ciclo_de_revisao],
    before_agent_callback=preparar_e_validar_entrada,
)
