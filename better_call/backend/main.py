import os
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from twilio.rest import Client
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads backend/.env if present

router = APIRouter()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "+18576637141")
TWIML_URL = os.getenv(
    "TWIML_URL",
    "https://handler.twilio.com/twiml/EH0ccb7a1d231ca96f31859460f376465d",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class CallRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str
    destination: str = Field(pattern=r"^\+\d{8,15}$")
    prompt: Optional[str] = ""


@router.get("/api/health")
def health():
    return {"ok": True}


def enrich_prompt(name: str, raw_prompt: str) -> str:

    try:
        client = OpenAI()  # usa OPENAI_API_KEY do ambiente
        # Instruções curtas e objetivas para um "prompt rewriter"
        instructions = (
            "Você é um reescritor de prompts para um agente de voz telefônico automatizado que fará uma ligação ativa. "
            "Sua tarefa é transformar o pedido original do usuário (geralmente curto ou incompleto) em um prompt rico, coerente e acionável, que possa ser usado pela API de Realtime Voice da OpenAI. "
            "O agente telefônico sempre deve iniciar a conversa de forma proativa, sem esperar input inicial do destinatário. "
            "Você deve identificar a intenção original, estruturar o papel/persona do agente (ex: coach agressivo, atendente simpático, terapeuta etc), adicionar exemplos de falas realistas que o agente pode usar, e formular perguntas ou variações úteis. "
            "O prompt resultante será passado para a API de voz: deve ser direto, em português, e pronto para uso. "
            "Personalize o prompt com o nome do usuário, quando fizer sentido. "
            "Saída: apenas o prompt final, em português, sem explicações, títulos ou marcações extras (ex: sem markdown)."
        )


        # Contexto de entrada com nome e prompt original
        input_text = f"""
        O seguinte pedido foi feito por um usuário para gerar uma ligação telefônica automatizada por voz.

        Nome do usuário: {name}

        Pedido original:
        \"\"\"{raw_prompt.strip()}\"\"\"

        Reescreva esse pedido como um prompt final e estruturado para um agente de voz que **ligará proativamente para alguém** e **iniciará a conversa sem esperar input**.

        Inclua no prompt final:
        - Persona do agente (ex: coach agressivo, atendente, terapeuta, etc).
        - Objetivo claro da ligação.
        - Estilo de fala (ex: bravo, informal, divertido, calmo...).
        - 6–10 exemplos de falas iniciais ou variações que o agente pode dizer.
        - 4–6 perguntas de follow-up que o agente pode fazer.
        - Regras práticas: o que o agente deve ou não fazer (do/don’t).
        - Passe o nome do usuário como contexto para o agente se referir a ele pelo nome.

        A saída deve ser apenas o prompt final que será passado diretamente para a OpenAI Realtime API.
        """


        # Responses API (padrão atual do SDK)
        resp = client.responses.create(
            model='gpt-4o-mini',
            instructions=instructions,
            input=input_text,
        )
        enriched = (resp.output_text or "").strip()
        return enriched
    except Exception:
        return raw_prompt


@router.post("/api/call")
def make_call(req: CallRequest, request: Request):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return JSONResponse(
            {"ok": False, "error": "Missing TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN"}, status_code=500
        )

    final_prompt = enrich_prompt(req.name, req.prompt or "")

    try:
        # Persist request to DB (shared instance on app.state.db)
        try:
            db = request.app.state.db
            if db is not None:
                db.insert_call_request(email=req.email, telefone=req.destination, prompt=final_prompt or "")
        except Exception:
            # Do not fail call if DB write fails
            pass


        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=req.destination,
            from_=TWILIO_FROM_NUMBER,
            url=TWIML_URL,
        )

        return {"ok": True, "call_sid": call.sid, "to": req.destination}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
