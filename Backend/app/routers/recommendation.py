from fastapi import APIRouter, HTTPException, Depends
from app.schemas import RecommendRequest, RecommendResponse, User
from app.services.llm_service import extract_with_groq
from app.routers.recsysmodel import recommend
from app.routers.auth import get_current_user_optional
# from sqlmodel import Session, select
# from app.database import engine
# from app.schemas import Place, PlaceDetailResponse # Import thêm Place và Schema mới

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendations(
    req: RecommendRequest, 
    # Cho phép user chưa đăng nhập cũng dùng được (Optional Auth)
    current_user: User = Depends(get_current_user_optional) 
):
    # 1. Gọi AI Service để trích xuất thông tin từ text
    extraction = await extract_with_groq(req.user_text)
    
    # 2. Gọi RecSys (Truyền user_id nếu đã đăng nhập để cá nhân hóa)
    user_id = current_user.id if current_user else None
    results_df = recommend(extraction, user_id)
    
    # 3. Chuyển đổi DataFrame sang PlaceOut schema
    results_list = []
    for _, row in results_df.head(req.top_k).iterrows():
        # Schema mới: Place có tags (List[str])
        tags = row.get('tags', [])
        if not isinstance(tags, list):
            tags = []
        
        place = {
            "id": int(row.get('id', 0)),
            "name": str(row.get('name', 'Unknown')),
            "country": "Vietnam",
            "province": tags[0] if tags else "Vietnam",  # Lấy tag đầu làm province tạm
            "region": "Vietnam",
            "themes": tags,
            "score": float(row.get('score', 0.0))
        }
        results_list.append(place)
    
    # 4. Trả về kết quả
    return RecommendResponse(extraction=extraction, results=results_list)

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