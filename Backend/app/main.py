from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from schemas import AuthenticatorResponse, ReviewerResponse
from analyzer import analyze_review_authenticity, analyze_product_review

app = FastAPI(
    title="ReviewShield API",
    version="1.0"
)

# CORS (important for React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # OK for hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "API is running"}

# ===== Review Authenticator Endpoint =====
@app.post("/analyze", response_model=AuthenticatorResponse)
async def analyze_review(image: UploadFile = File(...)):
    """Analyze a review image for authenticity."""
    try:
        # Read image file
        image_data = await image.read()
        
        result = analyze_review_authenticity(image_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Product Reviewer Endpoint =====
@app.post("/analyze-product", response_model=ReviewerResponse)
async def analyze_product(
    userRequirements: str = Form(...),
    specText: str = Form(...),
    specImage: Optional[UploadFile] = File(None)
):
    """Analyze product specifications against user requirements."""
    try:
        spec_image_data = None
        if specImage:
            spec_image_data = await specImage.read()
        
        result = analyze_product_review(
            user_requirements=userRequirements,
            spec_text=specText,
            spec_image=spec_image_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))