import os
import base64
import io
from PIL import Image
from transformers import pipeline
import google.generativeai as genai
from typing import Optional, Dict, List

# Initialize Hugging Face pipelines
_text_classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
_zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
_image_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def _summarize_with_gemini(review_text: str, rating: int) -> Dict[str, str]:
    """Generate product summary and rating suggestions using Gemini API."""
    try:
        if not GEMINI_API_KEY:
            return {"summary": "API key not configured", "suggested_rating": "N/A"}
        
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""Based on this product review (rating: {rating}/5), provide:
1. A concise product summary (2-3 sentences)
2. A suggested fair rating (1-5) based on the review content

Review: {review_text}

Format response as:
SUMMARY: [your summary]
SUGGESTED_RATING: [1-5]"""
        
        response = model.generate_content(prompt)
        response_text = response.text
        
        summary = "N/A"
        suggested_rating = "N/A"
        
        if "SUMMARY:" in response_text:
            summary = response_text.split("SUMMARY:")[1].split("SUGGESTED_RATING:")[0].strip()
        if "SUGGESTED_RATING:" in response_text:
            suggested_rating = response_text.split("SUGGESTED_RATING:")[1].strip()
        
        return {"summary": summary, "suggested_rating": suggested_rating}
    except Exception as e:
        return {"summary": f"Error: {str(e)}", "suggested_rating": "N/A"}

def _analyze_text(review_text: str, rating: int) -> Dict:
    """Analyze review text for authenticity signals."""
    signals = {}
    reasons = []
    risk_score = 0
    
    # 1. Sentiment analysis
    sentiment_result = _text_classifier(review_text[:512])[0]
    signals["sentiment"] = sentiment_result["label"]
    signals["sentiment_confidence"] = round(sentiment_result["score"], 2)
    
    # High positive sentiment with extreme rating can be suspicious
    if sentiment_result["label"] == "POSITIVE" and sentiment_result["score"] > 0.9 and rating == 5:
        risk_score += 20
        reasons.append("Extremely positive sentiment paired with 5-star rating (potential bias)")
    
    # 2. Zero-shot classification for review authenticity
    authenticity_labels = ["genuine review", "fake review", "spam review"]
    authenticity_result = _zero_shot_classifier(review_text[:512], authenticity_labels)
    top_label = authenticity_result["labels"][0]
    signals["authenticity_classification"] = top_label
    signals["authenticity_scores"] = {
        label: round(score, 2) 
        for label, score in zip(authenticity_result["labels"], authenticity_result["scores"])
    }
    
    if top_label in ["fake review", "spam review"]:
        risk_score += 30
        reasons.append(f"Classified as '{top_label}' by authenticity model")
    
    # 3. Text length analysis
    word_count = len(review_text.split())
    signals["word_count"] = word_count
    
    if word_count < 10 and rating in [1, 5]:
        risk_score += 15
        reasons.append("Very short review with extreme rating (1 or 5 stars)")
    
    # 4. Repetition check (simple heuristic)
    words = review_text.lower().split()
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        signals["word_uniqueness"] = round(unique_ratio, 2)
        if unique_ratio < 0.6:
            risk_score += 15
            reasons.append("High word repetition detected (potential copy-paste or template spam)")
    
    # 5. Rating-text mismatch
    if rating >= 4 and sentiment_result["label"] == "NEGATIVE":
        risk_score += 20
        reasons.append("High rating with negative sentiment (text-rating mismatch)")
    elif rating <= 2 and sentiment_result["label"] == "POSITIVE":
        risk_score += 20
        reasons.append("Low rating with positive sentiment (text-rating mismatch)")
    
    return {
        "signals": signals,
        "reasons": reasons,
        "risk_score": min(risk_score, 100)
    }

def _analyze_image(image_base64: str) -> Dict:
    """Analyze product image for authenticity signals."""
    signals = {}
    reasons = []
    risk_score = 0
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Image classification
        image_result = _image_classifier(image)
        top_result = image_result[0]
        
        signals["image_classification"] = top_result["label"]
        signals["image_confidence"] = round(top_result["score"], 2)
        
        # Image quality heuristic
        if image.size[0] < 100 or image.size[1] < 100:
            risk_score += 10
            reasons.append("Low resolution image (potential stock photo or manipulated)")
        
        signals["image_dimensions"] = f"{image.size[0]}x{image.size[1]}"
        
    except Exception as e:
        signals["image_error"] = str(e)
        risk_score += 5
    
    return {
        "signals": signals,
        "reasons": reasons,
        "risk_score": risk_score
    }

def analyze_review(review_text: str, rating: int, image_base64: Optional[str] = None) -> Dict:
    """Main function to analyze a product review for authenticity."""
    
    # Analyze text
    text_analysis = _analyze_text(review_text, rating)
    
    # Analyze image if provided
    image_analysis = {}
    if image_base64:
        image_analysis = _analyze_image(image_base64)
    
    # Combine risk scores
    total_risk = text_analysis["risk_score"] + image_analysis.get("risk_score", 0)
    if image_base64:
        average_risk = total_risk / 2
    else:
        average_risk = text_analysis["risk_score"]
    
    # Determine risk level
    if average_risk >= 70:
        risk_level = "CRITICAL"
    elif average_risk >= 50:
        risk_level = "HIGH"
    elif average_risk >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # Get Gemini summary
    gemini_result = _summarize_with_gemini(review_text, rating)
    
    # Combine all signals
    all_signals = {
        **text_analysis["signals"],
        **image_analysis.get("signals", {}),
        "overall_risk_score": round(average_risk, 1)
    }
    
    all_reasons = text_analysis["reasons"] + image_analysis.get("reasons", [])
    
    return {
        "risk_level": risk_level,
        "confidence": int(average_risk),
        "signals": all_signals,
        "reasons": all_reasons if all_reasons else ["Review appears authentic"],
        "product_summary": gemini_result.get("summary", "N/A"),
        "suggested_rating": gemini_result.get("suggested_rating", "N/A")
    }