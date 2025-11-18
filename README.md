## Empathy Chatbots (Avatar + Emoji)

Two small Gemini-powered chatbot prototypes for the empathy study:
- `avatar_chatbot.py`: drives a VTube Studio avatar with sentiment-driven facial expressions and speaks replies via TTS.
- `emoji_chatbot.py`: text-only chatbot that spices responses with emojis based on the same sentiment layer.

### Quick start
1) Requirements: Python 3.10+, running VTube Studio (for the avatar bot), and a Gemini API key.  
2) Install deps:
   ```bash
   python -m pip install -r requirements.txt
   ```
3) Create a `.env` in this folder:
   ```
   GEMINI_API_KEY=your_google_gemini_key
   # Optional (avatar chatbot):
   VTS_AUTH_TOKEN=token_from_vtube_studio
   VTS_URL=ws://localhost:8001
   ```
4) Emoji chatbot:
   ```bash
   python emoji_chatbot.py
   ```
5) Avatar chatbot (start VTube Studio first, load a model with hotkeys bound):
   ```bash
   python avatar_chatbot.py
   ```
   

### VTube Studio setup (avatar bot)
- Create/assign hotkeys in VTS for these expression names: `Happy`, `Neutral`, `Concern`, `Sad`, `Angry`. The code maps emotions → hotkey names in `DEFAULT_HOTKEYS` inside `avatar_chatbot.py`.
- On first run without `VTS_AUTH_TOKEN`, VTS will prompt you to approve the plugin; the script prints the token so you can add it to `.env` and reconnect without prompts.
- Connection details live in `vtube_studio_client.py` (WebSocket `ws://localhost:8001` by default). Update `VTS_URL` if you changed the port.

### How it works
- Gemini layer: `GeminiChatClient` wraps `google-generativeai` to keep chat history and return text replies.
- Emotion layer: `EmotionClassifier` uses VADER sentiment; compound scores are mapped to coarse emotions (`excited`, `happy`, `neutral`, `concerned`, `sad`, `angry`). The same tag drives either avatar expressions or emoji decoration.
- Emoji bot: After each Gemini reply, the classifier appends an emoji (`emotion_classifier.py`) and prints the tagged response.
- Avatar bot: After the reply, the classifier picks an expression hotkey, `VTubeStudioClient` triggers it, and `TextToSpeech` reads the response aloud (pyttsx3).

### Customization
- Swap hotkey names or add new ones in `DEFAULT_HOTKEYS` (avatar_chatbot.py).
- Adjust sentiment thresholds or emojis in `emotion_classifier.py`.
- Change speaking speed/voice in `tts.py`.
- Pick a different Gemini model by setting `GEMINI_MODEL` in `.env`. Default tries `gemini-1.5-flash-latest`, then falls back to `gemini-1.5-pro-latest`, `gemini-1.0-pro`, `gemini-pro`. If your key only supports a specific one, set it explicitly.

### Troubleshooting
- Missing token: run the avatar bot once without `VTS_AUTH_TOKEN` and approve the plugin in VTS; paste the printed token into `.env`.
- No avatar reaction: confirm VTS is running, the WebSocket port matches `VTS_URL`, and the hotkey names match `DEFAULT_HOTKEYS`.
- TTS issues on Windows: open Voice Settings (pyttsx3 uses the default SAPI voice). Reduce the rate in `tts.py` if speech clips.
