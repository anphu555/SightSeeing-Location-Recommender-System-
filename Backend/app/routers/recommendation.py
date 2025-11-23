from fastapi import APIRouter, HTTPException
from app.schemas import RecommendRequest, RecommendResponse
from app.services.llm_service import extract_with_groq
from app.services.scoring_service import rank_places

# api endpoint

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    # 1. Gọi AI Service để trích xuất thông tin
    extraction = await extract_with_groq(req.user_text)
    
    # 2. Gọi Scoring Service để tìm địa điểm
    results = rank_places(extraction, req.top_k)
    
    # 3. Trả về kết quả
    return RecommendResponse(extraction=extraction, results=results)