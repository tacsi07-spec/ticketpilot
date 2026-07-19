from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    ticket: str = Field(min_length=5, max_length=10_000)
    reply_language: str = Field(default="German")


class TicketAnalysis(BaseModel):
    problem_summary: str
    likely_causes: list[str]
    troubleshooting_steps: list[str]
    powershell_commands: list[str]
    security_notes: list[str]
    information_needed: list[str]
    estimated_resolution_time: str
    user_reply: str