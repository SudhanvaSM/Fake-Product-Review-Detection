def analyze_review(review_text: str, rating: int, image_base64=None):

    review_lower = review_text.lower()
    words = review_lower.split()

    score = 0
    reasons = []

    # 1. Short review + 5 stars
    if rating == 5 and len(words) < 10:
        score += 2
        reasons.append("Very short review paired with a 5-star rating")

    # 2. Generic praise detection
    generic_phrases = ["excellent", "very good", "amazing", "best product"]
    if any(phrase in review_lower for phrase in generic_phrases):
        score += 1
        reasons.append("Contains generic promotional language")

    # 3. Repetition check
    if len(set(words)) < len(words) * 0.6:
        score += 1
        reasons.append("High repetition of common words")

    # Risk mapping
    if score >= 3:
        risk = "High"
    elif score == 2:
        risk = "Medium"
    else:
        risk = "Low"

    confidence = min(60 + score * 10, 90)

    return {
        "risk_level": risk,
        "confidence": confidence,
        "signals": {
            "length_rating_mismatch": rating == 5 and len(words) < 10,
            "generic_language": any(p in review_lower for p in generic_phrases),
            "repetition_detected": len(set(words)) < len(words) * 0.6
        },
        "reasons": reasons
    }