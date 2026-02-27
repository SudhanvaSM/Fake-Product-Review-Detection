def analyze_review(review_text: str, rating: int, image_base64=None):
    # TEMP MOCK — replace with real logic later
    return {
        "risk_level": "High",
        "confidence": 78,
        "signals": {
            "ai_assisted_likelihood": 0.71,
            "tone": "overly_positive",
            "repetition": True,
            "length_rating_mismatch": True,
            "verified_purchase_visible": False
        },
        "reasons": [
            "Review uses generic praise with no product-specific details",
            "Extremely positive tone without mentioning drawbacks",
            "Short review paired with a 5-star rating"
        ]
    }