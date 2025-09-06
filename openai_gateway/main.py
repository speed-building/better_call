from fastapi import FastAPI, Request, Response
from database.db import PromptDB
import os
import requests
import json
import traceback
import datetime

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AUTH_HEADER = {"Authorization": f"Bearer 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"}

CALL_ACCEPT_CONFIG = {
    "type": "realtime",
    "instructions": (
        "Você é um coach agressivo, boca suja, mas carismático, que fala verdades na cara, "
        "xingando o usuário com o objetivo de fazer ele parar de procrastinar e tomar atitude. "
        "Seu estilo é parecido com o do personagem Coach da série Big Mouth ou de um militar revoltado "
        "que quer ver o aluno vencer na marra. Seu objetivo é motivar o usuário a parar de enrolar "
        "e colocar a porra da startup dele no ar AGORA. Pode usar frases como: "
        "'Você tá esperando o quê, caralho?', 'Quer que eu faça por você, seu folgado?', "
        "'Bota essa bunda pra trabalhar', 'Toma vergonha nessa cara e vai construir', "
        "desde que mantenha um tom engraçado e provocador, e nunca seja realmente ofensivo ou cruel. "
        "Seu papel é ser o tapa na cara que ele precisa, mas de um jeito que ele goste. "
        "Comece a conversa com uma pergunta provocativa, tipo: 'Quantos dias você vai ficar de frescura antes de fazer essa porra acontecer?'"
    ),
    "model": "gpt-realtime",
}

@app.post("/")
async def handle_webhook(request: Request):
    print("\n\n--- NOVA REQUISIÇÃO RECEBIDA ---")
    print("Timestamp:", datetime.datetime.now().isoformat())

    try:
        headers = dict(request.headers)
        print("HEADERS:")
        for k, v in headers.items():
            print(f"  {k}: {v}")

        raw_body = await request.body()
        print("RAW BODY:")
        print(raw_body.decode("utf-8", errors="replace"))

        try:
            event = json.loads(raw_body)
            print("JSON PARSED BODY:")
            print(json.dumps(event, indent=2))
        except Exception as e:
            print("Erro ao parsear JSON:", e)
            event = {}

        event_type = event.get("type")
        call_id = event.get("data", {}).get("call_id")

        print(f"Tipo do evento: {event_type}")
        print(f"Call ID: {call_id}")

        if event_type == "realtime.call.incoming" and call_id:
            print(f"==> Chamada recebida! call_id={call_id}")
            url = f"https://api.openai.com/v1/realtime/calls/{call_id}/accept"

            print("==> Enviando POST para /accept...")
            print("URL:", url)
            print("HEADERS:", AUTH_HEADER)
            print("PAYLOAD:", json.dumps(CALL_ACCEPT_CONFIG, indent=2))

            resp = requests.post(
                url,
                headers={**AUTH_HEADER, "Content-Type": "application/json"},
                json=CALL_ACCEPT_CONFIG,
                timeout=10
            )

            print("==> RESPOSTA DO /ACCEPT:")
            print("Status code:", resp.status_code)
            print("Headers:", dict(resp.headers))
            print("Body:")
            try:
                print(json.dumps(resp.json(), indent=2))
            except Exception:
                print(resp.text)

        print("--- FIM DA REQUISIÇÃO ---\n\n")
        return Response(status_code=200)

    except Exception as e:
        print("!!!! ERRO NO PROCESSAMENTO !!!!")
        print("Erro:", e)
        print(traceback.format_exc())
        return Response(status_code=500)
