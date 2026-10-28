# Notas de design

## Por que este desenho

- **Sequencial no topo**: cada etapa depende da anterior (sem pedido estruturado não há análise).
- **Paralelo nas análises**: fornecedor e preço são independentes e podem rodar ao mesmo tempo.
- **Ciclo redator/revisor**: separar quem escreve de quem critica melhora a consistência. O limite de 3 voltas evita custo e laço infinito.
- **Saída do ciclo por ferramenta**: o revisor chama `aprovar_recomendacao`, que define `actions.escalate = True`. É assim que o `LoopAgent` sabe que pode parar.

## Estado compartilhado

Cada agente grava sua saída com `output_key`. Os agentes seguintes leem com `{chave}` na instrução.

| Chave | Quem grava | Quem lê |
|---|---|---|
| `pedido_estruturado` | intake | analistas, redator |
| `analise_fornecedor` | analista_fornecedor | redator |
| `analise_preco` | analista_preco | redator |
| `recomendacao` | redator | revisor |
| `feedback_revisor` | revisor | redator |
| `chamadas_ferramenta` | guardrail | guardrail |

Atenção: chaves literais `{ }` em instruções são interpretadas como variáveis de estado. Por isso os textos de instrução não usam JSON com chaves.

## Guardrails

- **Entrada** (`before_agent_callback` no agente raiz): inicializa o estado e bloqueia entradas com CPF ou cartão antes de qualquer chamada ao modelo.
- **Ferramentas** (`before_tool_callback`): limita o total de chamadas por sessão.

## Como testar sem um LLM

O teste `test_workflow_fake_llm.py` troca o modelo de cada agente por uma subclasse de `BaseLlm` que devolve respostas e chamadas de ferramenta roteirizadas. Assim é possível conferir o estado da sessão e a saída do ciclo sem custo e sem rede. Ele valida a lógica do fluxo, não a qualidade de um modelo real.

## Possíveis evoluções

- Conjunto de avaliação com `adk eval` usando um modelo real.
- Migrar de `SequentialAgent`/`ParallelAgent`/`LoopAgent` para `Workflow` quando estável.
- Trocar `data.py` por uma fonte de dados real e sessões persistentes.
