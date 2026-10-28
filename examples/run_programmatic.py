"""Executa o workflow por código, sem a CLI.

Requer credenciais configuradas (veja .env.example). Rode da raiz do repositório:
    python -m examples.run_programmatic "Comprar 500 kg de resina PP da Beta a R$ 11,00"
"""

import asyncio
import sys

from dotenv import load_dotenv  # instalado junto com o google-adk
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from purchase_review.agent import root_agent

APP = "purchase_review"


async def main(texto: str) -> None:
    load_dotenv()
    sessoes = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP, session_service=sessoes)
    sessao = await sessoes.create_session(app_name=APP, user_id="demo")
    mensagem = types.Content(role="user", parts=[types.Part(text=texto)])

    async for evento in runner.run_async(
        user_id="demo", session_id=sessao.id, new_message=mensagem
    ):
        print(f"[{evento.author}]")

    final = await sessoes.get_session(app_name=APP, user_id="demo", session_id=sessao.id)
    print("\nRecomendação:\n", final.state.get("recomendacao", "(sem recomendação)"))


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "Comprar 500 kg de resina PP da Beta a R$ 11,00"))
