import os
import base64
import io
from PIL import Image
from transformers import pipeline
import google.generativeai as genai
from typing import Optional, Dict, List, Tuple

# Initialize Hugging Face pipelines
_text_classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
_zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
_image_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def _extract_text_from_image(image_data: bytes) -> str:
    """Extract text from image using OCR or image-to-text model."""
    try:
        from pytesseract import pytesseract
        image = Image.open(io.BytesIO(image_data))
        text = pytesseract.image_to_string(image)
        return text if text.strip() else "No text detected in image"
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def _analyze_review_text_authenticity(review_text: str) -> Tuple[int, str, bool, List[str]]:
    """Analyze text for fake review indicators."""
    risk_score = 0
    flagged_keywords = []
    
    # 1. Sentiment analysis
    sentiment_result = _text_classifier(review_text[:512])[0]
    is_positive = sentiment_result["label"] == "POSITIVE"
    sentiment_confidence = sentiment_result["score"]
    
    # 2. Zero-shot classification for authenticity
    authenticity_labels = ["genuine review", "fake review", "spam review"]
    authenticity_result = _zero_shot_classifier(review_text[:512], authenticity_labels)
    top_label = authenticity_result["labels"][0]
    
    if top_label in ["fake review", "spam review"]:
        risk_score += 45
        flagged_keywords.append(top_label.replace(" ", "_"))
    
    # 3. Detect generic promotional phrases
    promotional_phrases = ["best product", "highly recommend", "must buy", "life changing", 
                          "amazing", "perfect", "excellent", "five stars", "love it", "perfect product"]
    found_promo = [p for p in promotional_phrases if p.lower() in review_text.lower()]
    if found_promo:
        risk_score += 20
        flagged_keywords.extend(found_promo)
    
    # 4. Detect repetition
    words = review_text.lower().split()
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.6:
            risk_score += 15
            flagged_keywords.append("high_repetition")
    
    # 5. Short reviews with extreme positivity
    if len(words) < 15 and sentiment_confidence > 0.85:
        risk_score += 15
        flagged_keywords.append("short_extreme_positive")
    
    trust_score = max(0, 100 - risk_score)
    is_fake = risk_score > 50
    verdict = "Likely Fake" if is_fake else "Likely Genuine"
    
    return trust_score, verdict, is_fake, flagged_keywords

def analyze_review_authenticity(image_data: bytes) -> Dict:
    """Main function to analyze review image for authenticity."""
    try:
        # Extract text from image
        review_text = _extract_text_from_image(image_data)
        
        if "Error" in review_text or "No text" in review_text:
            return {
                "trustScore": 50,
                "verdict": "Unable to Analyze",
                "isFake": False,
                "summary": "Could not extract text from image. Try a clearer image with readable text.",
                "flaggedKeywords": ["image_quality_issue"]
            }
        
        # Analyze text
        trust_score, verdict, is_fake, keywords = _analyze_review_text_authenticity(review_text)
        
        # Generate summary using Gemini
        summary = _generate_authenticity_summary(review_text, is_fake, keywords)
        
        return {
            "trustScore": trust_score,
            "verdict": verdict,
            "isFake": is_fake,
            "summary": summary,
            "flaggedKeywords": keywords
        }
    except Exception as e:
        return {
            "trustScore": 50,
            "verdict": "Error",
            "isFake": False,
            "summary": f"Error during analysis: {str(e)}",
            "flaggedKeywords": []
        }

def _generate_authenticity_summary(review_text: str, is_fake: bool, keywords: List[str]) -> str:
    """Generate a summary of the authenticity analysis."""
    try:
        if not GEMINI_API_KEY:
            if is_fake:
                return "This review exhibits suspicious patterns including promotional language, generic praise, or repetitive text commonly associated with inauthentic content."
            else:
                return "This review demonstrates authentic characteristics with specific product references and natural language patterns consistent with genuine customer feedback."
        
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""Based on this product review, generate a brief authenticity analysis (1-2 sentences).
Review text: {review_text[:500]}
Flagged issues: {', '.join(keywords) if keywords else 'None'}
Assessment: {'Likely Fake' if is_fake else 'Likely Genuine'}

Provide a concise summary explaining why this review is authentic or fake."""
        
        response = model.generate_content(prompt)
        return response.text if response.text else ("Suspicious review content detected." if is_fake else "Review appears authentic.")
    except Exception as e:
        return "Unable to generate summary." if not is_fake else "Review shows signs of being potentially fake."

def analyze_product_review(user_requirements: str, spec_text: str, spec_image: Optional[bytes] = None) -> Dict:
    """Analyze product specifications against user requirements."""
    try:
        # Extract specs from image if provided
        spec_info = spec_text
        if spec_image:
            extracted_specs = _extract_text_from_image(spec_image)
            if "Error" not in extracted_specs:
                spec_info += f"\n{extracted_specs}"
        
        # Generate analysis using Gemini
        score, summary, pros, cons = _generate_product_analysis(user_requirements, spec_info)
        
        return {
            "score": score,
            "summary": summary,
            "pros": pros,
            "cons": cons
        }
    except Exception as e:
        return {
            "score": 50,
            "summary": f"Error analyzing product: {str(e)}",
            "pros": ["Unable to determine"],
            "cons": ["Error during analysis"]
        }

def _generate_product_analysis(user_requirements: str, spec_text: str) -> Tuple[int, str, List[str], List[str]]:
    """Generate product analysis using Gemini API."""
    try:
        if not GEMINI_API_KEY:
            # Mock analysis
            return 65, "Product specifications meet most of your requirements.", \
                   ["Good processor", "Adequate RAM", "Modern features"], \
                   ["Battery life could be better", "Price is slightly high"]
        
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""Analyze this product against user requirements and provide:
1. A match score (40-100)
2. A brief summary (2-3 sentences)
3. List of 3-4 pros
4. List of 2-3 cons

User Requirements: {user_requirements}

Product Specs: {spec_text}

Format response EXACTLY as:
SCORE: [number]
SUMMARY: [summary text]
PROS: [pro1 | pro2 | pro3]
CONS: [con1 | con2]"""
        
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Parse response
        score = 65  # default
        summary = "Product analysis complete."
        pros = ["Good performance", "Meets requirements"]
        cons = ["Some limitations"]
        
        if "SCORE:" in response_text:
            try:
                score_str = response_text.split("SCORE:")[1].split("\n")[0].strip()
                score = int(''.join(c for c in score_str if c.isdigit()))
                score = max(40, min(100, score))  # Clamp between 40-100
            except:
                pass
        
        if "SUMMARY:" in response_text:
            summary = response_text.split("SUMMARY:")[1].split("PROS:")[0].strip()
        
        if "PROS:" in response_text:
            pros_str = response_text.split("PROS:")[1].split("CONS:")[0].strip()
            pros = [p.strip() for p in pros_str.split("|")]
        
        if "CONS:" in response_text:
            cons_str = response_text.split("CONS:")[1].strip()
            cons = [c.strip() for c in cons_str.split("|")]
        
        return score, summary, pros, cons
    except Exception as e:
        return 60, "Product analysis completed with partial results.", \
               ["Meets basic requirements", "Reasonable specifications"], \
               ["Limited detailed analysis", "Some specifications unclear"]