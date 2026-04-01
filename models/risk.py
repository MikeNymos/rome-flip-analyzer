"""
Risicobeoordeling en beschrijvingsanalyse (NLP).
"""
from __future__ import annotations


from data.constants import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, RED_FLAGS


def analyze_description(text: str) -> dict:
    """
    Analyseert de Italiaanse beschrijving van een listing op relevante keywords.

    Returns:
        Dict met positieve en negatieve indicatoren en een beschrijvingsscore.
    """
    if not text:
        return {
            "positive": [],
            "negative": [],
            "red_flags": [],
            "description_score": 50,  # Neutraal bij geen beschrijving
        }

    text_lower = text.lower()
    positive = []
    negative = []
    red_flags = []

    for keyword, label in POSITIVE_KEYWORDS.items():
        if keyword in text_lower:
            positive.append({"keyword": keyword, "label": label})

    for keyword, label in NEGATIVE_KEYWORDS.items():
        if keyword in text_lower:
            negative.append({"keyword": keyword, "label": label})

    for keyword, penalty in RED_FLAGS.items():
        if keyword in text_lower:
            red_flags.append({"keyword": keyword, "penalty": penalty})

    # Bereken beschrijvingsscore (50 = neutraal, 0-100 range)
    score = 50
    score += len(positive) * 5
    score -= len(negative) * 8
    for rf in red_flags:
        score += rf["penalty"]  # penalty is al negatief

    score = max(0, min(100, score))

    return {
        "positive": positive,
        "negative": negative,
        "red_flags": red_flags,
        "description_score": score,
    }
