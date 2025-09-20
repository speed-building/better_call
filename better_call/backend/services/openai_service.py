from typing import Optional
from openai import OpenAI

from ..core.config import settings
from ..core.exceptions import OpenAIServiceError


class OpenAIService:
    """Service for handling OpenAI API interactions."""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise OpenAIServiceError("OpenAI API key is not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def enrich_prompt(self, name: str, raw_prompt: str) -> str:
        """
        Enrich a raw prompt using OpenAI to create a structured prompt for voice calls.
        
        Args:
            name: Name of the user making the request
            raw_prompt: Original prompt from the user
            
        Returns:
            Enriched prompt ready for voice API
            
        Raises:
            OpenAIServiceError: If the API call fails
        """
        try:
            instructions = (
                "Você é um reescritor de prompts para um agente de voz telefônico automatizado que fará uma ligação ativa. "
                "Sua tarefa é transformar o pedido original do usuário (geralmente curto ou incompleto) em um prompt rico, coerente e acionável, que possa ser usado pela API de Realtime Voice da OpenAI. "
                "O agente telefônico sempre deve iniciar a conversa de forma proativa, sem esperar input inicial do destinatário. "
                "Você deve identificar a intenção original, estruturar o papel/persona do agente (ex: coach agressivo, atendente simpático, terapeuta etc), adicionar exemplos de falas realistas que o agente pode usar, e formular perguntas ou variações úteis. "
                "O prompt resultante será passado para a API de voz: deve ser direto, em português, e pronto para uso. "
                "Personalize o prompt com o nome do usuário, quando fizer sentido. "
                "Saída: apenas o prompt final, em português, sem explicações, títulos ou marcações extras (ex: sem markdown)."
            )

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
            - Regras práticas: o que o agente deve ou não fazer (do/don't).
            - Passe o nome do usuário como contexto para o agente se referir a ele pelo nome.

            A saída deve ser apenas o prompt final que será passado diretamente para a OpenAI Realtime API.
            """

            response = self.client.responses.create(
                model='gpt-4o-mini',
                instructions=instructions,
                input=input_text,
            )
            
            enriched = (response.output_text or "").strip()
            return enriched if enriched else raw_prompt
            
        except Exception as e:
            # Log the error but don't fail the call - return original prompt
            print(f"OpenAI enrichment failed: {e}")
            return raw_prompt
