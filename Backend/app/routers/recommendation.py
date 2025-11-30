from fastapi import APIRouter, HTTPException, Depends
from app.schemas import RecommendRequest, RecommendResponse
from app.services.llm_service import extract_with_groq
from app.routers.recsysmodel import recommend # Import hàm mới viết
from app.auth import get_current_user_optional

router = APIRouter()

@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendations(
    req: RecommendRequest, 
    # Cho phép user chưa đăng nhập cũng dùng được (Optional Auth)
    username: str = Depends(get_current_user_optional) 
):
    # 1. Gọi AI Service để trích xuất thông tin từ text
    extraction = await extract_with_groq(req.user_text)
    
    # 2. Gọi RecSys (Truyền thêm username để cá nhân hóa)
    results_df = recommend(extraction, username)
    
    # 3. Chuyển đổi DataFrame sang PlaceOut schema
    # Map các cột từ CSV sang schema chuẩn
    results_list = []
    for _, row in results_df.head(req.top_k).iterrows():
        # Parse themes từ tourism_type (có thể là chuỗi phân cách bằng dấu phẩy)
        themes_str = str(row.get('tourism_type', ''))
        themes = [t.strip() for t in themes_str.split(',') if t.strip()] if themes_str else []
        
        place = {
            "id": int(row.get('id', 0)),
            "name": str(row.get('name', 'Unknown')),
            "country": "Vietnam",  # Mặc định vì dữ liệu là Việt Nam
            "province": str(row.get('province', 'Unknown')),
            "region": str(row.get('province', 'Unknown')),  # Tạm dùng province làm region
            "themes": themes if themes else ['tourism'],
            "score": float(row.get('score', 0.0))
        }
        results_list.append(place)
    
    # 4. Trả về kết quả
    return RecommendResponse(extraction=extraction, results=results_list)