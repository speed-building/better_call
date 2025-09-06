from fastapi import APIRouter, Request, Response
import os
import requests
import json
import traceback
import datetime

router = APIRouter(prefix="/openai-gateway")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AUTH_HEADER = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

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

@router.post("/")
async def handle_webhook(request: Request):
    try:

        raw_body = await request.body()

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
            # Get last prompt from shared DB
            last_prompt = None
            try:
                db = request.app.state.db
                if db is not None:
                    last_prompt = db.get_last_prompt()
            except Exception:
                pass

            # Merge last prompt into instructions if present
            payload = dict(CALL_ACCEPT_CONFIG)
            if last_prompt:
                payload = dict(payload)
                payload["instructions"] = last_prompt

            url = f"https://api.openai.com/v1/realtime/calls/{call_id}/accept"

            print("==> Enviando POST para /accept...")
            print("URL:", url)
            print("HEADERS:", AUTH_HEADER)
            print("PAYLOAD:", json.dumps(payload, indent=2))

            resp = requests.post(
                url,
                headers={**AUTH_HEADER, "Content-Type": "application/json"},
                json=payload,
                timeout=10
            )

            print("==> Resposta do /accept:")
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
