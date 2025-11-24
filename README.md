## Empathy Chatbots (Web Live2D + Emoji)

Gemini-powered chatbots for the empathy study:
- `web_live2d_chatbot.py`: serves a browser-based Live2D avatar and feeds it emotion tags over WebSocket.
- `emoji_chatbot.py`: text-only chatbot that spices responses with emojis based on the same sentiment layer.

### Quick start
1) Requirements: Python 3.10+ and a Gemini API key.
2) Install deps:
   ```bash
   python -m pip install -r requirements.txt
   ```
3) Create a `.env` in this folder:
   ```
   GEMINI_API_KEY=your_google_gemini_key
   GEMINI_MODEL=gemini-2.5-flash # can use other models, but highly suggest this one
   # Optional: Azure TTS for spoken replies
   # AZURE_SPEECH_KEY=...
   # AZURE_SPEECH_REGION=eastus
   ```
4) Web Live2D chatbot:
   ```bash
   python web_live2d_chatbot.py
   ```
   Then open http://localhost:8000/ in your browser. The page connects to the chatbot via WebSocket (ws://localhost:8765), swaps expressions, and includes an on-page chat box. For a simple text-only browser chat, open http://localhost:8000/emoji.html.
5) Emoji web chatbot:
   ```bash
   python emoji_chatbot.py
   ```
   Then open http://localhost:8002/emoji.html (WebSocket ws://localhost:8766).

### Web Live2D setup
- Place your Live2D model files under `web_avatar/...` and set the path in `web_avatar/index.html` via `MODEL_PATH`, or pass `?model=relative/path/to/your.model3.json` in the URL.
- Expression names matching the emotion map (`Happy/Neutral/Concern/Sad/Angry`) will be used if present; otherwise the page falls back to simple parameter tweaks.
- Status is shown in the top-right; subtitles and chat input are centered at the bottom.

### How it works
- Gemini layer: `GeminiChatClient` wraps `google-generativeai` to keep chat history and return text replies.
- Emotion layer: `EmotionClassifier` uses VADER + keyword overrides; compound scores map to `excited`, `happy`, `neutral`, `concerned`, `sad`, `angry`.
- Emoji bot: After each reply, the classifier appends an emoji (`emotion_classifier.py`) and prints the tagged response.
- Web Live2D bot: A minimal HTTP server hosts `web_avatar/index.html`; the chatbot streams `{emotion, reply}` via WebSocket. The page loads a Live2D model, applies expressions, and shows chat/status overlays.
- TTS (optional): `tts.py` uses Azure Cognitive Services; if keys are present, `web_live2d_chatbot.py` will speak replies and log `[tts]` on synthesis.

### Customization
- Adjust sentiment thresholds or emojis in `emotion_classifier.py`.
- Change speaking speed/voice in `tts.py` (Azure).
- Pick a different Gemini model via `GEMINI_MODEL` in `.env`.
- Web avatar: set `MODEL_PATH` in `web_avatar/index.html` or pass `?model=...` in the browser URL; adjust the emotion↔expression map in the JS if names differ.

### Troubleshooting
- No expressions: ensure your model has matching `*.exp3.json` entries listed in its `.model3.json`.
- TTS silent: confirm `AZURE_SPEECH_KEY/REGION` are set; the server logs `[info] TTS ready` on init and `[tts] ...` on synthesis.
- Connection: WebSocket endpoint is `ws://localhost:8765`; HTTP is `http://localhost:8000/`.
