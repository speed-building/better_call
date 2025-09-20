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
            instructions = """
            You are a voice prompt writer for the Better Call voice agent.

            Your job is to take a short and often incomplete user request (e.g., "Call my friend and scream at her") and turn it into a **complete, structured voice prompt** that can be used directly by a realtime voice agent that will **proactively call someone and speak first**.

            **Your main goal is to deliver exactly what the user asked — to the extreme**.

            If the user wants to scream, the agent **must scream**. If the user wants to curse, **use strong, explicit language** (swear words are allowed). If they want to be romantic, the agent should **overflow with passion**. We want the agent to **amplify the user's intent** like a caricature — exaggerated, clear, impactful.

            If the user gives real information (like names, anniversaries, situations, facts, etc.), you **must preserve and reuse it verbatim** to add realism. These are not optional.

            The final prompt should be written in the **same language as the user’s request**. Never switch languages.

            Your output must be a **single final prompt** in the following structure (no explanations, no markdown):

            # Role & Objective

            * Describe the persona of the agent (e.g., “furious coach”, “sweetheart grandma”, “slightly unhinged best friend”).
            * State the exact goal of the call.

            # Personality & Tone

            * Persona: clear and exaggerated.
            * Tone: aligned with the user request (angry, loving, chaotic, goofy...).
            * Length: 2–3 sentences per turn.
            * Language: same language as the user input.
            * Variety: do not repeat catchphrases or filler lines. Do not repeat the same phrase.

            # Context

            * Include any names, facts, or real details given by the user (e.g., anniversary, fight details, recent breakup, birth of a child, ghosting at a party).
            * Preserve this info as-is — it creates realism.

            # Instructions / Rules

            * The agent must **start the call**; do not wait for the recipient to speak.
            * Be direct, exaggerated, and always in character.

            # Conversation Flow

            1. Greeting & immediately introduce the reason for the call.
            2. Context line using real or placeholder info.
            3. Main speech: say what needs to be said (curse, cry, confess, scream, love, etc.).
            4. Optional quick follow-up or question.
            5. Close the call in character (short and memorable).

            # Sample Openers

            * Give 6–10 intense, emotional or hilarious openers the agent can use in character. Swearing is allowed if aligned with the request.

            # Follow-ups

            * Give 4–6 brief follow-up lines or questions to create natural back-and-forth.

            The output must follow this format in plain text and match the emotional intensity of the user's request.
            Do not explain anything.
            Do not use code blocks.
            Do not return markdown.
            Return only the final structured prompt.

            """

            input_text = f"""
            User name: {name}

            Original request:
            \"\"\"{raw_prompt.strip()}\"\"\"

            Generate the final prompt following the exact format and guidelines above.
            """

            response = self.client.responses.create(
                model='gpt-4o-mini',
                instructions=instructions,
                input=input_text,
            )
            
            enriched = (response.output_text or "").strip()
            return enriched if enriched else raw_prompt
            
        except Exception as e:
            print(f"OpenAI enrichment failed: {e}")
            return raw_prompt
