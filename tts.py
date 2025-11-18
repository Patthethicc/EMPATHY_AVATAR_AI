from __future__ import annotations

import os
import azure.cognitiveservices.speech as speechsdk


class TextToSpeech:
    """
    Microsoft Azure TTS helper using Ashley voice (Neuro-sama's voice).
    """

    def __init__(
        self,
        voice: str = "en-US-AshleyNeural",
        rate: str = "27%",  # Speed adjustment: -50% to +100%
        pitch: str = "+45Hz",  # Pitch adjustment: -50Hz to +50Hz
        output_format: speechsdk.SpeechSynthesisOutputFormat = speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3,
    ) -> None:
        api_key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        if not api_key:
            raise ValueError("AZURE_SPEECH_KEY is missing from .env file")
        
        # Configure Azure Speech SDK
        speech_config = speechsdk.SpeechConfig(
            subscription=api_key,
            region=region
        )
        # Use a higher quality output format to reduce artifacts.
        speech_config.speech_synthesis_output_format = output_format
        
        # Set the voice
        speech_config.speech_synthesis_voice_name = voice
        
        # Force default speaker output (explicit, some installs ignore None)
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        print(f"[info] Azure TTS initialized with voice: {voice}")

    def say(self, text: str) -> None:
        """Speak the given text using Azure TTS."""
        if not text:
            return
        
        try:
            # Build SSML with rate and pitch adjustments
            ssml = f"""
            <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
                <voice name='{self.voice}'>
                    <prosody rate='{self.rate}' pitch='{self.pitch}'>
                        {self._escape_xml(text)}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Synthesize speech
            result = self.synthesizer.speak_ssml_async(ssml).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                pass  # Success
            else:
                cancellation = result.cancellation_details
                print(f"[warn] Azure TTS not completed: {result.reason} {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"[warn] Error details: {cancellation.error_details}")
        
        except Exception as exc:
            print(f"[warn] Azure TTS error: {exc}")

    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters in text."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    def stop(self) -> None:
        """Stop any ongoing synthesis."""
        # Azure doesn't need explicit stop for synchronous synthesis
        pass


# Alternative voices you can try:
# - "en-US-AshleyNeural" - Young female (Neuro-sama base)
# - "en-US-JennyNeural" - Friendly female
# - "en-US-AriaNeural" - Expressive female
# - "en-US-SaraNeural" - Soft female
# 
# To adjust for Neuro's higher pitch, try:
# TextToSpeech(pitch="+5Hz") or TextToSpeech(pitch="+10Hz")
