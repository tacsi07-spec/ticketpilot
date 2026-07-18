import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "Az OPENAI_API_KEY hiányzik. Ellenőrizd a backend/.env fájlt."
    )

client = OpenAI(api_key=api_key)

app = FastAPI(
    title="TicketPilot API",
    description="AI Assistant for IT Support Engineers",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
def home():
    return {"message": "TicketPilot API is running 🚀"}


@app.post("/analyze", response_model=TicketAnalysis)
def analyze_ticket(data: TicketRequest) -> TicketAnalysis:
    ticket_text = data.ticket.strip()
    reply_language = data.reply_language.strip()

    if reply_language not in {"German", "English"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported reply language.",
        )

    if not ticket_text:
        raise HTTPException(
            status_code=400,
            detail="A ticket szövege nem lehet üres.",
        )

    try:
        response = client.responses.parse(
            model="gpt-5-mini",
            instructions="""
You are TicketPilot, a senior Microsoft IT support engineer.

Your task is to analyze IT support tickets accurately and safely.

Primary areas:
- Windows 10 and Windows 11
- Microsoft 365
- Active Directory
- Microsoft Entra ID
- Exchange Online
- Microsoft Intune
- VPN and authentication
- PowerShell troubleshooting

Rules:
- Do not invent information that is not present in the ticket.
- Separate confirmed facts from assumptions.
- Order troubleshooting steps from safest and simplest to most advanced.
- Do not recommend destructive actions unless absolutely necessary.
- Warn about administrator permissions, service interruption,
  security impact, data loss, or account lockout risks.
- PowerShell commands must be directly usable where possible.
- Do not wrap PowerShell commands in Markdown code fences.
- If no PowerShell command is necessary, return an empty list.
- If important information is missing, list exactly what the technician
  should collect next.
- Create a short, professional end-user reply.
- The reply must be written in the requested language.
- Do not expose internal technical reasoning unnecessarily.
- Do not claim that the issue is solved unless the ticket confirms it.
- Use a polite business tone.
- When more information is required, clearly ask the user for it.
""",
            input=f"""
IT SUPPORT TICKET:

{ticket_text}

Generate the end-user reply in: {reply_language}
""",
            text_format=TicketAnalysis,
        )

        analysis = response.output_parsed

        if analysis is None:
            raise RuntimeError("Az AI nem adott feldolgozható választ.")

        return analysis

    except HTTPException:
        raise

    except Exception as error:
        print(f"OpenAI API error: {error}")

        raise HTTPException(
            status_code=500,
            detail=(
                "Az AI-elemzés sikertelen volt. "
                "Ellenőrizd a backend terminálját, az API-kulcsot "
                "és az API-egyenleget."
            ),
        )