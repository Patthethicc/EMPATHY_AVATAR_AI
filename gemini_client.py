from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import List, Optional, Sequence

import google.generativeai as genai


@dataclass
class GeminiChatClient:
    """
    Lightweight wrapper around the Gemini chat API that keeps conversational state.
    """

    api_key: str
    model: str = "gemini-1.5-flash-latest"
    system_prompt: Optional[str] = None
    chat: genai.ChatSession = field(init=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing.")

        genai.configure(api_key=self.api_key)
        # Allow overriding the model via env (GEMINI_MODEL) without code edits.
        requested_model = os.getenv("GEMINI_MODEL") or self.model
        candidates: Sequence[str] = (
            requested_model,
            "gemini-1.5-pro-latest",
            "gemini-1.0-pro",
            "gemini-pro",
        )

        last_error: Optional[Exception] = None
        for model_name in candidates:
            try:
                model = genai.GenerativeModel(
                    model_name,
                    system_instruction=self.system_prompt
                    or (
                        "You are an empathetic, warm listener. "
                        "Acknowledge feelings with sensitivity, mirror the user's tone, and validate their emotions. "
                        "Use concise, calm language. Offer support before solutions. Avoid stating limitations about being an AI; "
                        "focus on being present and caring. "
                    ),
                )
                self.chat = model.start_chat(history=[])
                self.model = model_name  # record which one succeeded
                break
            except Exception as exc:
                last_error = exc
        else:
            raise RuntimeError(f"Failed to init Gemini client. Tried models: {candidates}") from last_error

    def reply(self, user_message: str) -> str:
        response = self.chat.send_message(user_message)
        return response.text.strip()

    def history(self) -> List[str]:
        return [item.parts[0].text for item in self.chat.history]  # type: ignore[index]
