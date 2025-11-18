from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

KEYWORD_MAP = {
    "angry": "angry",
    "mad": "angry",
    "furious": "angry",
    "rage": "angry",
    "irritated": "angry",
    "annoyed": "angry",
    "upset": "sad",
    "sad": "sad",
    "depressed": "sad",
    "down": "sad",
    "unhappy": "sad",
    "happy": "happy",
    "glad": "happy",
    "pleased": "happy",
    "excited": "excited",
    "thrilled": "excited",
    "concern": "concerned",
    "worried": "concerned",
    "anxious": "concerned",
    "nervous": "concerned",
    "uneasy": "concerned",
    "neutral": "neutral",
    "calm": "neutral",
}

EMOTION_TO_EMOJI: Dict[str, str] = {
    "excited": "🤩",
    "happy": "😊",
    "neutral": "😐",
    "concerned": "😟",
    "sad": "😔",
    "angry": "😠",
}


@dataclass
class EmotionClassifier:
    """
    Simple sentiment-based emotion mapper.
    """

    analyzer: SentimentIntensityAnalyzer = SentimentIntensityAnalyzer()

    def classify(self, text: str) -> Tuple[str, float]:
        scores = self.analyzer.polarity_scores(text or "")
        compound = scores.get("compound", 0.0)

        # Quick keyword override to make intent like "be concerned" map directly.
        lowered = (text or "").lower()
        for word, mapped in KEYWORD_MAP.items():
            if word in lowered:
                return mapped, compound

        # Tighter neutral band and adjusted cutoffs:
        # excited: very positive, happy: solid positive, sad/angry: clearer negatives,
        # concern: mid-level non-neutral that isn't strongly +/-.
        if compound >= 0.7:
            emotion = "excited"
        elif compound >= 0.45:
            emotion = "happy"
        elif compound <= -0.65:
            emotion = "angry"
        elif compound <= -0.35:
            emotion = "sad"
        elif -0.05 <= compound <= 0.05:
            emotion = "neutral"
        else:
            emotion = "concerned"

        return emotion, compound

    def add_emoji(self, text: str, emotion: str) -> str:
        emoji = EMOTION_TO_EMOJI.get(emotion, "")
        if emoji and emoji not in text:
            return f"{text} {emoji}"
        return text
