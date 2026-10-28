"""Guardrails operacionais: validação de entrada e limite de chamadas de ferramenta."""

import re
from typing import Optional

from google.genai import types

CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CARTAO_RE = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")

MENSAGEM_BLOQUEIO = (
    "Não posso processar esta solicitação porque ela parece conter dados pessoais "
    "sensíveis (CPF ou número de cartão). Remova esses dados e envie novamente."
)

MAX_CHAMADAS_FERRAMENTA = 8


def contem_dado_sensivel(texto: str) -> bool:
    """Retorna True se o texto parece conter CPF ou número de cartão."""
    return bool(CPF_RE.search(texto) or CARTAO_RE.search(texto))


def _texto_do_conteudo(conteudo: Optional[types.Content]) -> str:
    if conteudo is None or not conteudo.parts:
        return ""
    return " ".join(p.text for p in conteudo.parts if getattr(p, "text", None))


def preparar_e_validar_entrada(callback_context) -> Optional[types.Content]:
    """before_agent_callback do agente raiz.

    1) Inicializa o estado compartilhado da sessão.
    2) Se a entrada tiver dado sensível, devolve uma resposta pronta. Ao devolver
       um Content, o ADK pula a execução do agente e nada é enviado ao modelo.
    """
    estado = callback_context.state
    if "feedback_revisor" not in estado:
        estado["feedback_revisor"] = "(nenhum feedback ainda)"
    if "chamadas_ferramenta" not in estado:
        estado["chamadas_ferramenta"] = 0

    texto = _texto_do_conteudo(getattr(callback_context, "user_content", None))
    if contem_dado_sensivel(texto):
        return types.Content(role="model", parts=[types.Part(text=MENSAGEM_BLOQUEIO)])
    return None


def limitar_chamadas_ferramenta(tool, args, tool_context) -> Optional[dict]:
    """before_tool_callback: limita o total de chamadas de ferramenta por sessão.

    Devolver um dicionário substitui a execução da ferramenta pelo resultado
    devolvido; devolver None deixa a ferramenta rodar normalmente.
    """
    usadas = tool_context.state.get("chamadas_ferramenta", 0)
    if usadas >= MAX_CHAMADAS_FERRAMENTA:
        return {
            "status": "blocked",
            "mensagem": f"Limite de {MAX_CHAMADAS_FERRAMENTA} chamadas de ferramenta atingido.",
        }
    tool_context.state["chamadas_ferramenta"] = usadas + 1
    return None
