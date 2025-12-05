from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database import get_session
from app.schemas import RecommendRequest, RecommendResponse, User
from app.services.llm_service import extract_with_groq
from app.routers.recsysmodel import recommend_two_tower
from app.routers.auth import get_current_user_optional
# Import hàm mới viết ở Bước 1
from app.services.recsys_utils import build_profile_from_history 

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendations(
    req: RecommendRequest, 
    current_user: User = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    # --- 1. Short-term Interest (Từ câu chat hiện tại) ---
    extraction = await extract_with_groq(req.user_text)
    current_intent_tags = extraction.location # Giả sử map location/type sang tags
    
    # --- 2. Long-term Interest (Từ lịch sử click/view/like) ---
    historical_tags = []
    if current_user:
        # Tự động "đào" tags từ lịch sử thay vì bắt user nhập
        historical_tags = build_profile_from_history(current_user.id, session)
        
        # Nếu muốn kết hợp cả "User tự khai" (preferences) nếu có
        if current_user.preferences:
             historical_tags.extend(current_user.preferences)
    
    # --- 3. Kết hợp (Hybrid Strategy) ---
    # Ưu tiên câu chat hiện tại. Nếu user chỉ chat "Hello" hoặc không tìm cụ thể,
    # hệ thống sẽ fallback về historical_tags để gợi ý cái họ thường thích.
    if current_intent_tags and len(current_intent_tags) > 0:
        final_tags = current_intent_tags
        # Có thể trộn thêm 20% sở thích cũ để đa dạng hóa (tùy chọn)
    else:
        final_tags = historical_tags

    # --- 4. Xử lý Cold Start (Người dùng mới tinh, chưa like gì, chưa chat gì) ---
    if not final_tags:
        # Default tags cho người mới
        final_tags = ["Vietnam", "Nature", "Food"] 

    # --- 5. Gọi Model Two-Tower ---
    # Đảm bảo final_tags là list unique strings
    final_tags = list(set(final_tags))
    
    results_df = recommend_two_tower(final_tags, top_k=req.top_k)
    
    # ... (Code chuyển đổi sang PlaceOut giữ nguyên) ...
    results_list = []
    for _, row in results_df.iterrows():
        # ... logic cũ ...
        tags = row.get('tags', [])
        results_list.append({
            "id": int(row.get('id', 0)),
            "name": str(row.get('name', 'Unknown')),
            "country": "Vietnam",
            "province": tags[0] if tags else "Vietnam",
            "themes": tags,
            "score": float(row.get('score', 0.0))
        })

    return RecommendResponse(extraction=extraction, results=results_list)