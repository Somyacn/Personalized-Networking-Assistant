import re
from typing import List

# Global variable to cache the classifier pipeline
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

# Rule-based fallback keywords mapping
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
    """Lazily load the Hugging Face zero-shot classification pipeline."""
    global _classifier
    if _classifier is None:
        try:
            from transformers import pipeline
            # DistilBERT MNLI zero shot model
            _classifier = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli"
            )
        except Exception as e:
            print(f"Failed to load Hugging Face zero-shot classifier: {e}")
            print("Falling back to keyword-based analyzer.")
            _classifier = None
    return _classifier

def _analyze_by_keywords(description: str) -> List[str]:
    """Fallback rule-based classification using keywords."""
    description_lower = description.lower()
    scores = {theme: 0 for theme in CANDIDATE_THEMES}
    
    for theme, keywords in KEYWORDS_MAPPING.items():
        for keyword in keywords:
            # Match word boundary to avoid partial matches (e.g. 'ai' in 'pain')
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, description_lower))
            scores[theme] += matches
            
    # Sort and filter themes that have at least one keyword match
    matched_themes = [theme for theme, count in scores.items() if count > 0]
    matched_themes.sort(key=lambda x: scores[x], reverse=True)
    
    # Return top matched themes, or default to general if none match
    if not matched_themes:
        return ["Social & Networking"]
    return matched_themes[:3]

def analyze_event_description(description: str, mock: bool = False) -> List[str]:
    """Extracts themes from event description using zero-shot classification or keyword fallback.
    
    Args:
        description: Text description of the event.
        mock: If True, forces keyword-based matching bypassing the transformer.
    """
    if not description.strip():
        return ["Social & Networking"]
        
    if mock:
        return _analyze_by_keywords(description)
        
    classifier = _get_classifier()
    if classifier is None:
        return _analyze_by_keywords(description)
        
    try:
        result = classifier(description, CANDIDATE_THEMES)
        # Result keys: sequence, labels, scores
        # We take labels with a confidence score > 0.15, or at least the top label
        extracted = []
        for label, score in zip(result["labels"], result["scores"]):
            if score > 0.15 or not extracted:
                extracted.append(label)
        return extracted[:3]  # Limit to top 3 themes
    except Exception as e:
        print(f"Error during model classification: {e}")
        return _analyze_by_keywords(description)
