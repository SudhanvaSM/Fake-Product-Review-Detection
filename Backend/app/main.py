from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ReviewRequest, AnalysisResponse
from .analyzer import analyze_review

app = FastAPI(
    title="Fake Product Review Detection API",
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

@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: ReviewRequest):
    try:
        result = analyze_review(
            review_text=request.review_text,
            rating=request.rating,
            image_base64=request.image
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))