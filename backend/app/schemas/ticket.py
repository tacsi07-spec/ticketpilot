from pydantic import BaseModel


class TicketRequest(BaseModel):
    ticket: str
    reply_language: str


class TicketAnalysis(BaseModel):
    category: str
    priority: str
    priority_reason: str
    confidence_score: int
    confidence_reason: str
    problem_summary: str
    likely_causes: list[str]
    troubleshooting_steps: list[str]
    powershell_commands: list[str]
    security_notes: list[str]
    information_needed: list[str]
    estimated_resolution_time: str
    user_reply: str