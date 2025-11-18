from __future__ import annotations

import os

from dotenv import load_dotenv

from emotion_classifier import EmotionClassifier
from gemini_client import GeminiChatClient


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    gemini = GeminiChatClient(api_key=api_key)
    classifier = EmotionClassifier()

    print("Emoji Chatbot ready. Type 'exit' to quit.\n")

    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        reply = gemini.reply(user)

        # Prefer user's emotion when it's strongly negative/positive; fall back to reply tone.
        user_emotion, user_score = classifier.classify(user)
        bot_emotion, bot_score = classifier.classify(reply)
        if abs(user_score) >= 0.35:
            emotion, score = user_emotion, user_score
        else:
            emotion, score = bot_emotion, bot_score
        decorated = classifier.add_emoji(reply, emotion)
        print(f"Bot [{emotion} | {score:+.2f}]: {decorated}")


if __name__ == "__main__":
    main()
