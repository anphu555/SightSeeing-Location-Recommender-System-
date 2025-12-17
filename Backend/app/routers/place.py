from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from sqlalchemy import or_
from app.database import get_session
from app.schemas import Place, PlaceDetailResponse
from typing import List
import re

router = APIRouter()

# Stop words - các từ phổ biến không mang ý nghĩa tìm kiếm
STOP_WORDS = {
    # English
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 
    'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 
    'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
    'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 
    'don', 'should', 'now', 'want', 'go', 'going', 'would', 'could', 'like',
    'need', 'looking', 'find', 'see', 'visit', 'show', 'please', 'get', 'give',
    # Vietnamese
    'tôi', 'muốn', 'đi', 'đến', 'một', 'các', 'những', 'là', 'có', 'được',
    'cho', 'và', 'của', 'trong', 'với', 'này', 'đó', 'thì', 'mà', 'như',
    'nơi', 'ở', 'tại', 'hay', 'hoặc', 'cần', 'xem', 'tìm', 'kiếm'
}

def extract_keywords(query: str) -> List[str]:
    """Trích xuất từ khóa có ý nghĩa từ câu query"""
    # Chuyển thành lowercase và tách từ
    words = re.findall(r'\b\w+\b', query.lower())
    # Loại bỏ stop words và từ quá ngắn (< 2 ký tự)
    keywords = [word for word in words if word not in STOP_WORDS and len(word) >= 2]
    return keywords

@router.get("/{place_id}", response_model=PlaceDetailResponse)
def get_place_detail(place_id: int, session: Session = Depends(get_session)):
    """
    API lấy thông tin chi tiết của một địa điểm dựa trên ID.
    Frontend gọi: GET /api/v1/place/{id}
    Ví dụ: /api/v1/place/5
    """
    # Tìm địa điểm trong database theo ID
    place = session.get(Place, place_id)
    
    if not place:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm này")
    
    # Lấy province từ tags[0] nếu có
    province = place.tags[0] if place.tags and len(place.tags) > 0 else None
    
    # Trả về dữ liệu với province
    return PlaceDetailResponse(
        id=place.id,
        name=place.name,
        description=place.description,
        image=place.image,
        tags=place.tags,
        province=province
    )

@router.get("/search/by-name", response_model=List[PlaceDetailResponse])
def search_places_by_name(
    q: str = Query(..., description="Tên địa điểm hoặc câu mô tả cần tìm"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng kết quả tối đa"),
    session: Session = Depends(get_session)
):
    """
    API tìm kiếm địa điểm theo tên hoặc từ khóa (case-insensitive, partial match).
    Hỗ trợ tìm kiếm cả câu như "i want to go to the beach" bằng cách trích xuất từ khóa.
    Frontend gọi: GET /api/v1/place/search/by-name?q=ha+long&limit=20
    """
    if not q or len(q.strip()) < 2:
        return []
    
    # Trích xuất từ khóa có ý nghĩa từ câu query
    keywords = extract_keywords(q)
    
    # Nếu không tìm được từ khóa nào, thử tìm với toàn bộ query gốc
    if not keywords:
        keywords = [q.strip()]
    
    # Tạo điều kiện OR cho tất cả từ khóa - tìm trong cả name và description
    conditions = []
    for keyword in keywords:
        search_term = f"%{keyword}%"
        conditions.append(Place.name.ilike(search_term))
        conditions.append(Place.description.ilike(search_term))
    
    statement = select(Place).where(or_(*conditions)).limit(limit)
    
    places = session.exec(statement).all()
    
    # Convert to PlaceDetailResponse with province
    results = []
    for place in places:
        province = place.tags[0] if place.tags and len(place.tags) > 0 else None
        results.append(PlaceDetailResponse(
            id=place.id,
            name=place.name,
            description=place.description,
            image=place.image,
            tags=place.tags,
            province=province
        ))
    
    return results