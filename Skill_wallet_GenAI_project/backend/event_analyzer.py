import re
from typing import List

_classifier = None

CANDIDATE_THEMES = [
    "Technology",
    "Business & Entrepreneurship",
    "Finance & Investment",
    "Marketing & Sales",
    "Design & Creative",
    "Science & Research",
    "Healthcare & Wellness",
    "Career Development",
    "Social & Networking",
    "Education & Academia"
]

KEYWORDS_MAPPING = {
    "Technology": ["tech", "software", "developer", "code", "ai", "data", "web", "computer", "digital", "algorithm", "robotics", "cybersecurity"],
    "Business & Entrepreneurship": ["business", "startup", "founder", "entrepreneur", "corporate", "management", "strategy", "enterprise", "leadership"],
    "Finance & Investment": ["finance", "vc", "invest", "money", "funding", "crypto", "blockchain", "stock", "banking", "capital", "wealth"],
    "Marketing & Sales": ["marketing", "sales", "seo", "brand", "growth", "advertising", "customer", "retail", "commerce", "social media"],
    "Design & Creative": ["design", "ux", "ui", "art", "creative", "product", "architecture", "fashion", "graphics", "media"],
    "Science & Research": ["science", "research", "academic", "physics", "biology", "chemistry", "lab", "quantum", "space", "discovery"],
    "Healthcare & Wellness": ["health", "wellness", "medical", "doctor", "fitness", "nutrition", "mental", "clinic", "medicine", "therapy"],
    "Career Development": ["career", "resume", "job", "hiring", "interview", "mentor", "recruit", "portfolio", "skills", "talent"],
    "Social & Networking": ["social", "mixer", "happy hour", "meetup", "networking", "party", "community", "gathering", "drinks", "chat"],
    "Education & Academia": ["education", "learn", "school", "university", "student", "teach", "workshop", "course", "lecture", "study"]
}


def _get_classifier():
    global _classifier
    if _classifier is None:
        try:
            from transformers import pipeline
            _classifier = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli"
            )
        except Exception:
            _classifier = None
    return _classifier


def _analyze_by_keywords(description: str) -> List[str]:
    description_lower = description.lower()
    scores = {theme: 0 for theme in CANDIDATE_THEMES}

    for theme, keywords in KEYWORDS_MAPPING.items():
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, description_lower))
            scores[theme] += matches

    matched = [t for t, c in scores.items() if c > 0]
    matched.sort(key=lambda x: scores[x], reverse=True)

    if not matched:
        return ["Social & Networking"]

    return matched[:3]


def analyze_event_description(description: str, mock: bool = False) -> List[str]:
    if not description.strip():
        return ["Social & Networking"]

    # ✅ FIX FOR PYTEST
    if mock:
        return_analyze_by_keywords(descriptions)
    classifier = _get_classifier()
    if classifier is None:
        return _analyze_by_keywords(description)

    try:
        result = classifier(description, CANDIDATE_THEMES)

        extracted = []
        for label, score in zip(result["labels"], result["scores"]):
            if score > 0.15 or not extracted:
                extracted.append(label)

        return extracted[:3]

    except Exception:
        return _analyze_by_keywords(description)