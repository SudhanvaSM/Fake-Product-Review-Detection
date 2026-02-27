from typing import Optional, List, Dict
from pydantic import BaseModel

# Review Authenticator Response
class AuthenticatorResponse(BaseModel):
    trustScore: int
    verdict: str
    isFake: bool
    summary: str
    flaggedKeywords: List[str]

# Product Reviewer Response
class ReviewerResponse(BaseModel):
    score: int
    summary: str
    pros: List[str]
    cons: List[str]