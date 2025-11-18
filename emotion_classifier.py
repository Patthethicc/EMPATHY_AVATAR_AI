from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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

        if compound >= 0.65:
            emotion = "excited"
        elif compound >= 0.25:
            emotion = "happy"
        elif compound <= -0.65:
            emotion = "angry"
        elif compound <= -0.25:
            emotion = "sad"
        elif -0.15 <= compound <= 0.15:
            emotion = "neutral"
        else:
            emotion = "concerned"

        return emotion, compound

    def add_emoji(self, text: str, emotion: str) -> str:
        emoji = EMOTION_TO_EMOJI.get(emotion, "")
        if emoji and emoji not in text:
            return f"{text} {emoji}"
        return text

