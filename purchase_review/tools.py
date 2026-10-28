"""Ferramentas (function tools) usadas pelos agentes.

As docstrings são lidas pelo modelo para decidir quando e como chamar cada
ferramenta, por isso descrevem argumentos e retorno com clareza.
"""

import unicodedata

from google.adk.tools import ToolContext

from .data import FORNECEDORES, PRECOS_REFERENCIA


def _normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem espaços nas pontas, para busca tolerante."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.lower().split())


def consultar_historico_fornecedor(fornecedor: str) -> dict:
    """Consulta o histórico de entregas de um fornecedor nos últimos 12 meses.

    Args:
        fornecedor: nome do fornecedor, por exemplo "Alfa Parafusos".

    Returns:
        Um dicionário com status "success" e os campos fornecedor, entregas_12m,
        otif_pct (percentual de entregas no prazo) e nao_conformidades.
        Se o fornecedor não existir, status "not_found" e uma mensagem.
    """
    registro = FORNECEDORES.get(_normalizar(fornecedor))
    if registro is None:
        return {"status": "not_found", "mensagem": f"Fornecedor '{fornecedor}' não encontrado."}
    return {
        "status": "success",
        "fornecedor": registro["nome"],
        "entregas_12m": registro["entregas_12m"],
        "otif_pct": round(100 * registro["entregas_no_prazo"] / registro["entregas_12m"], 1),
        "nao_conformidades": registro["nao_conformidades"],
    }


def consultar_preco_referencia(item: str, preco_unitario_ofertado: float) -> dict:
    """Compara o preço unitário ofertado com o preço de referência do item.

    Args:
        item: nome do item, por exemplo "Resina PP".
        preco_unitario_ofertado: preço unitário ofertado pelo fornecedor, em reais.

    Returns:
        Um dicionário com status "success", preco_ref, unidade, desvio_pct
        (positivo quando o ofertado é maior que a referência) e
        dentro_da_tolerancia (booleano). Se o item não existir, status "not_found".
    """
    registro = PRECOS_REFERENCIA.get(_normalizar(item))
    if registro is None:
        return {"status": "not_found", "mensagem": f"Item '{item}' sem preço de referência."}
    desvio = (preco_unitario_ofertado - registro["preco_ref"]) / registro["preco_ref"] * 100
    return {
        "status": "success",
        "preco_ref": registro["preco_ref"],
        "unidade": registro["unidade"],
        "desvio_pct": round(desvio, 1),
        "dentro_da_tolerancia": desvio <= registro["tolerancia_pct"],
    }


def aprovar_recomendacao(tool_context: ToolContext) -> dict:
    """Aprova a recomendação atual e encerra o ciclo de revisão.

    Deve ser chamada pelo revisor somente quando a recomendação cita o
    fornecedor, o preço e traz uma decisão clara.
    """
    # escalate = True faz o LoopAgent sair do ciclo.
    tool_context.actions.escalate = True
    return {"status": "success", "mensagem": "Recomendação aprovada; encerrando o ciclo de revisão."}
