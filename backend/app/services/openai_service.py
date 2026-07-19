from openai import OpenAI

from app.prompts.ticket_prompt import TICKET_ANALYSIS_INSTRUCTIONS
from app.schemas.ticket import TicketAnalysis


class OpenAIService:
    def __init__(self, client: OpenAI):
        self.client = client

    def analyze_ticket(
        self,
        ticket_text: str,
        reply_language: str,
    ) -> TicketAnalysis:
        response = self.client.responses.parse(
            model="gpt-5-mini",
            instructions=TICKET_ANALYSIS_INSTRUCTIONS,
            input=f"""
IT SUPPORT TICKET:

{ticket_text}

Generate the end-user reply in: {reply_language}
""",
            text_format=TicketAnalysis,
        )

        analysis = response.output_parsed

        if analysis is None:
            raise RuntimeError("The AI returned no structured response.")

        return analysis