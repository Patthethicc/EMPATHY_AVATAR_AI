from __future__ import annotations

import asyncio
import os
from typing import List

from dotenv import load_dotenv

from emotion_classifier import EmotionClassifier
from gemini_client import GeminiChatClient
from tts import TextToSpeech
from vtube_studio_client import VTubeStudioClient


DEFAULT_HOTKEYS = {
    "excited": "Happy",
    "happy": "Happy",
    "neutral": "Neutral",
    "concerned": "Concern",
    "sad": "Sad",
    "angry": "Angry",
}



async def run_avatar_chat() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    vts_token = os.getenv("VTS_AUTH_TOKEN")
    gemini = GeminiChatClient(api_key=api_key)
    classifier = EmotionClassifier()
    tts = TextToSpeech()
    speak_tasks: List[asyncio.Task] = []
    
    avatar = VTubeStudioClient(
        auth_token=vts_token,
        emotion_hotkeys=DEFAULT_HOTKEYS,
    )

    avatar_ready = False
    try:
        await avatar.connect()
        avatar_ready = True
        print("[info] Connected to VTube Studio. Expressions will follow the chatbot's tone.")
    except Exception as exc:
        print(f"[warn] VTube Studio not connected: {exc}")
        print("[warn] The chat will continue without avatar expressions.\n")

    print("Avatar Chatbot ready. Type 'exit' to quit.\n")

    tts_lock = asyncio.Lock()

    while True:
        user = await asyncio.to_thread(input, "You: ")
        if user.lower().strip() in {"exit", "quit"}:
            print("Goodbye!")
            break

        reply = await asyncio.to_thread(gemini.reply, user)

        # Prefer the user's tone when clearly expressed; otherwise use bot reply tone.
        user_emotion, user_score = classifier.classify(user)
        bot_emotion, bot_score = classifier.classify(reply)
        if abs(user_score) >= 0.35:
            emotion, score = user_emotion, user_score
        else:
            emotion, score = bot_emotion, bot_score

        if avatar_ready:
            try:
                await avatar.apply_emotion(emotion)
            except Exception as exc:
                print(f"[warn] Failed to trigger avatar expression: {exc}")
                avatar_ready = False

        print(f"Bot [{emotion} | {score:+.2f}]: {reply}")

        
        # Speak in the background so the prompt comes back immediately.
        async def speak_async(text: str) -> None:
            try:
                async with tts_lock:
                    await asyncio.to_thread(tts.say, text)
            except Exception as exc:
                print(f"[warn] TTS error: {exc}")

        task = asyncio.create_task(speak_async(reply))
        speak_tasks.append(task)

    # Tear down after loop exits. Use timeouts so exit can't hang.
    if avatar_ready:
        try:
            await asyncio.wait_for(avatar.close(), timeout=5)
        except Exception:
            pass

    # Cancel/finish any pending speech so we can exit promptly.
    for task in speak_tasks:
        if not task.done():
            task.cancel()
    if speak_tasks:
        try:
            await asyncio.wait_for(asyncio.gather(*speak_tasks, return_exceptions=True), timeout=5)
        except Exception:
            pass
    tts.stop()

if __name__ == "__main__":
    asyncio.run(run_avatar_chat())
