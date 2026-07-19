import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from app.schemas.ticket import TicketAnalysis, TicketRequest
from app.services.openai_service import OpenAIService


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "Az OPENAI_API_KEY hiányzik. Ellenőrizd a backend/.env fájlt."
    )

client = OpenAI(api_key=api_key)
openai_service = OpenAIService(client)

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
        return openai_service.analyze_ticket(
            ticket_text=ticket_text,
            reply_language=reply_language,
        )

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