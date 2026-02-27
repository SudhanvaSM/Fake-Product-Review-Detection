from typing import Optional, List, Dict
from pydantic import BaseModel

class ReviewRequest(BaseModel):
    review_text: str
    rating: int
    image: Optional[str] = None  # base64 image (optional)

class AnalysisResponse(BaseModel):
    risk_level: str
    confidence: int
    signals: Dict[str, object]
    reasons: List[str]
    product_summary: Optional[str] = None
    suggested_rating: Optional[str] = None