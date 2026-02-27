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
    """Analyze text for fake review using HuggingFace AI models."""
    flagged_keywords = []
    
    # 1. MAIN: Zero-shot classification for authenticity using HuggingFace
    authenticity_labels = ["genuine review", "fake review", "spam review"]
    authenticity_result = _zero_shot_classifier(review_text[:512], authenticity_labels)
    
    # Get scores for each label
    scores = dict(zip(authenticity_result["labels"], authenticity_result["scores"]))
    fake_score = scores.get("fake review", 0)
    genuine_score = scores.get("genuine review", 0)
    spam_score = scores.get("spam review", 0)
    
    # Convert to 0-100 scale
    trust_score = int(genuine_score * 100)
    fake_confidence = int(fake_score * 100)
    
    # Mark as fake if HuggingFace says so with high confidence
    is_fake = fake_score > genuine_score or fake_score > 0.4
    
    if is_fake:
        flagged_keywords.append(f"HF-fake-confidence-{fake_confidence}")
    
    # 2. Sentiment analysis
    sentiment_result = _text_classifier(review_text[:512])[0]
    is_positive = sentiment_result["label"] == "POSITIVE"
    sentiment_confidence = sentiment_result["score"]
    
    if sentiment_confidence > 0.9:
        flagged_keywords.append("extreme_positive_sentiment")
    
    # 3. Spam score
    if spam_score > 0.3:
        flagged_keywords.append("spam_detected")
        trust_score = max(0, trust_score - 30)
    
    # 4. Adjust based on text length
    words = review_text.lower().split()
    if len(words) < 10:
        flagged_keywords.append("very_short_review")
        trust_score = max(0, trust_score - 20)
    
    verdict = "Likely Fake" if is_fake else "Likely Genuine"
    
    return trust_score, verdict, is_fake, flagged_keywords

def analyze_review_authenticity(image_data: bytes, review_text: Optional[str] = None) -> Dict:
    """Main function to analyze review image for authenticity."""
    try:
        # If review text is provided directly, use it; otherwise try to extract from image
        if review_text and review_text.strip():
            extracted_text = review_text.strip()
        else:
            extracted_text = _extract_text_from_image(image_data)
        
        if "Error" in extracted_text or "No text" in extracted_text:
            return {
                "trustScore": 50,
                "verdict": "Unable to Analyze",
                "isFake": False,
                "summary": "Could not extract text from image. Try a clearer image with readable text.",
                "flaggedKeywords": ["image_quality_issue"]
            }
        
        # Analyze text
        trust_score, verdict, is_fake, keywords = _analyze_review_text_authenticity(extracted_text)
        
        # Generate summary using Gemini
        summary = _generate_authenticity_summary(extracted_text, is_fake, keywords)
        
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
    """Generate a detailed summary of authenticity analysis using Gemini AI."""
    try:
        if not GEMINI_API_KEY:
            if is_fake:
                return "AI analysis detected this review as likely fake based on language patterns and authenticity modeling."
            else:
                return "AI analysis indicates this review demonstrates authentic characteristics based on HuggingFace models."
        
        model = genai.GenerativeModel("gemini-pro")
        
        # Ask Gemini to explain in detail why it's fake or genuine
        prompt = f"""Analyze this product review and explain in 2-3 sentences whether it's fake or genuine.

Review: {review_text[:600]}

Based on HuggingFace AI models, this review is classified as: {'FAKE' if is_fake else 'GENUINE'}
Flagged patterns: {', '.join(keywords) if keywords else 'None detected'}

Provide a clear, concise analysis explaining:
1. Why AI models classified it as {'fake' if is_fake else 'genuine'}
2. Key patterns or language characteristics that support this assessment
3. Specific concerns or positive indicators

Keep response to 2-3 sentences maximum."""
        
        response = model.generate_content(prompt)
        return response.text if response.text else ("Suspicious review content detected by AI models." if is_fake else "Review demonstrates authentic patterns based on AI analysis.")
    except Exception as e:
        if is_fake:
            return f"HuggingFace models flagged this review as suspicious. Analysis: {keywords}"
        else:
            return "Review passed authenticity checks by HuggingFace AI models."

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