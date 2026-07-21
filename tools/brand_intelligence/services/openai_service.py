from __future__ import annotations

from openai import OpenAI


class OpenAIService:
    """
    Shared OpenAI client for the Brand Intelligence package.
    The client is created lazily on first use.
    """

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI()

        return self._client


openai_service = OpenAIService()