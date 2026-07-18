import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel


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
    ticket: str


@app.get("/")
def home():
    return {"message": "TicketPilot API is running 🚀"}


@app.post("/analyze")
def analyze_ticket(data: TicketRequest):
    ticket_text = data.ticket.strip()

    if not ticket_text:
        raise HTTPException(
            status_code=400,
            detail="A ticket szövege nem lehet üres.",
        )

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            instructions="""
You are a senior Microsoft IT support engineer.

Analyze the user's IT support ticket carefully.

Focus primarily on:
- Windows 10 and Windows 11
- Microsoft 365
- Active Directory
- Exchange Online
- Microsoft Intune
- VPN and authentication problems
- PowerShell troubleshooting

Answer in clear professional English.

Use exactly these sections:

Problem Summary
Likely Causes
Troubleshooting Steps
PowerShell Commands
Security Notes
Estimated Resolution Time

Important rules:
- Do not invent facts that are not present in the ticket.
- Clearly mark assumptions.
- Put PowerShell commands inside code blocks.
- Warn the technician before destructive or security-sensitive actions.
- If information is missing, state what should be collected next.
""",
            input=ticket_text,
        )

        return {
            "ticket_received": ticket_text,
            "analysis": response.output_text,
        }

    except Exception as error:
        print(f"OpenAI API error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Az AI-elemzés sikertelen volt. Ellenőrizd az API-kulcsot és az API-egyenleget.",
        )