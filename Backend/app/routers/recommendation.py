from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from collections import Counter
from typing import List
import ast

from app.schemas import RecommendRequest, RecommendResponse, User, PlaceOut, Rating, Place
from app.database import get_session
from app.routers.auth import get_current_user_optional
from app.services.llm_service import extract_with_groq
from app.routers.recsysmodel import recommend_two_tower 
# from sqlmodel import Session, select
# from app.database import engine
# from app.schemas import Place, PlaceDetailResponse # Import thêm Place và Schema mới

router = APIRouter()

def get_history_tags(user_id: int, session: Session, limit=5) -> List[str]:
    """Lấy tags từ những nơi user đã tương tác tốt (score >= 3.0)"""
    statement = select(Rating).where(Rating.user_id == user_id, Rating.score >= 3.0)
    ratings = session.exec(statement).all()
    
    tags_pool = []
    for r in ratings:
        place = session.get(Place, r.place_id)
        if place and place.tags:
            tags_pool.extend(place.tags)
            
    if not tags_pool: return []
    # Lấy top tags xuất hiện nhiều nhất
    return [tag for tag, _ in Counter(tags_pool).most_common(limit)]

@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendations(
    req: RecommendRequest,
    current_user: User = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    # ==========================
    # 1. SHORT-TERM INTENT (Từ Input Text + Groq)
    # ==========================
    current_intent_tags = []
    extraction = None
    
    if req.user_text and len(req.user_text.strip()) > 0:
        # Gọi Groq để hiểu ý định (đây là cái bạn đã tin tưởng)
        extraction = await extract_with_groq(req.user_text)
        
        # --- QUAN TRỌNG: Flatten GroqOutput thành Tags ---
        # Groq trả về object (type, budget...), ta cần biến nó thành list strings cho Two-Tower
        
        # 1. Location (Ưu tiên cao nhất)
        if extraction.location:
            current_intent_tags.extend(extraction.location)
            
        # 2. Type (Vd: "Nature", "Historical"...)
        if extraction.type and extraction.type.lower() != "none":
            current_intent_tags.append(extraction.type)
            
        # 3. Budget (Vd: "Cheap", "Luxury" - nếu trong data tags của bạn có)
        if extraction.budget and extraction.budget.lower() != "none":
            current_intent_tags.append(extraction.budget)

        # 4. Weather/Crowded (Nếu data tags có, vd: "Sunny", "Quiet")
        if extraction.weather and extraction.weather.lower() != "none":
            current_intent_tags.append(extraction.weather)
    
    # ==========================
    # 2. LONG-TERM PREFERENCE (Từ Lịch sử & Profile)
    # ==========================
    history_tags = []
    if current_user:
        # Lấy từ hành vi (Click, Like)
        history_tags = get_history_tags(current_user.id, session)
        # Lấy từ profile tĩnh (nếu có lúc đăng ký)
        if current_user.preferences:
            history_tags.extend(current_user.preferences)

    # ==========================
    # 3. HYBRID STRATEGY (Kết hợp)
    # ==========================
    # Logic: Nếu user đang tìm kiếm (có intent), dùng intent là chính.
    # Lịch sử chỉ dùng để bổ trợ hoặc fill nếu intent quá ít thông tin.
    
    final_tags = []
    
    if current_intent_tags:
        # Lấy intent làm trọng tâm
        final_tags = current_intent_tags 
        # Bổ sung thêm 2-3 tags sở thích mạnh nhất của user để lọc kết quả phù hợp gu
        if history_tags:
            # Chỉ lấy những tag lịch sử không trùng với intent hiện tại
            additional_tags = [t for t in history_tags if t not in current_intent_tags][:3]
            final_tags.extend(additional_tags)
    else:
        # Nếu không gõ gì (Trang chủ), dùng hoàn toàn lịch sử
        final_tags = history_tags
    
    # Fallback cho user mới tinh
    if not final_tags:
        final_tags = ["Vietnam", "Nature", "Beach"] # Default trending tags

    # Clean duplicates
    final_tags = list(set(final_tags))

    # ==========================
    # 4. PREDICT & RETURN
    # ==========================
    # Truyền tags vào Two-Tower model
    results_df = recommend_two_tower(final_tags, top_k=req.top_k)
    
    results_list = []
    for _, row in results_df.iterrows():
        # Parse tags từ string sang list nếu cần
        tags_raw = row.get('tags', [])
        
        # Nếu tags là string (JSON representation), parse nó
        if isinstance(tags_raw, str):
            try:
                tags = ast.literal_eval(tags_raw)
            except:
                tags = []
        else:
            tags = tags_raw if tags_raw else []
        # Lấy place từ database để có ảnh
        place = session.get(Place, int(row.get('id')))
        
        # Đảm bảo tags là list
        if not isinstance(tags, list):
            tags = []
        
        results_list.append(PlaceOut(
            id=int(row.get('id')),
            name=str(row.get('name')),
            province=tags[0] if tags else "Vietnam",
            themes=tags,
            score=float(row.get('score', 0.0)),
            image=place.image if place and place.image else None
        ))

    return RecommendResponse(extraction=extraction, results=results_list)

@router.get("/debug/vocabulary")
async def get_vocabulary():
    """Debug endpoint để xem vocabulary của model"""
    from app.routers.recsysmodel import loaded_mlb
    
    if loaded_mlb is None:
        return {"error": "Model not loaded yet"}
    
    vocab = list(loaded_mlb.classes_)
    return {
        "total_tags": len(vocab),
        "sample_tags": vocab[:50],  # Hiển thị 50 tags đầu
        "all_tags": vocab  # Toàn bộ vocabulary
    }

# @router.get("/place/{place_id}", response_model=PlaceDetailResponse)
# def get_place_detail(place_id: int):
#     with Session(engine) as session:
#         # Truy vấn địa điểm theo ID
#         place = session.get(Place, place_id)

#         if not place:
#             raise HTTPException(status_code=404, detail="Place not found")

#         # Trả về dữ liệu
#         return PlaceDetailResponse(
#             id=place.id,
#             name=place.name,
#             description=place.description, # Lấy description từ DB
#             image=place.image,             # Lấy ảnh từ DB
#             tags=place.tags
#         )