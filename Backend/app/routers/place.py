from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from sqlalchemy import or_, String
from app.database import get_session
from app.schemas import Place, PlaceDetailResponse
from app.services.llm_service import extract_with_groq
from typing import List
import re
import unicodedata

router = APIRouter()

def remove_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt"""
    nfkd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

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
    """Trích xuất từ khóa có ý nghĩa từ câu query, giữ nguyên cụm từ ghép (tên tỉnh/thành phố)"""
    query_lower = query.lower()
    
    # Bước 1: Loại bỏ stop words từ đầu và cuối câu, giữ nguyên phần còn lại
    words = re.findall(r'\b\w+\b', query_lower)
    
    # Tìm vị trí bắt đầu và kết thúc của phần có ý nghĩa
    start_idx = 0
    end_idx = len(words)
    
    # Loại bỏ stop words từ đầu
    while start_idx < len(words) and words[start_idx] in STOP_WORDS:
        start_idx += 1
    
    # Loại bỏ stop words từ cuối
    while end_idx > start_idx and words[end_idx - 1] in STOP_WORDS:
        end_idx -= 1
    
    if start_idx >= end_idx:
        return []
    
    # Giữ nguyên cụm từ còn lại (có thể là tên địa danh ghép như "Quang Ninh", "Ha Long")
    meaningful_phrase = ' '.join(words[start_idx:end_idx])
    
    return [meaningful_phrase] if meaningful_phrase else []

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
async def search_places_by_name(
    q: str = Query(..., description="Tên địa điểm hoặc câu mô tả cần tìm"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng kết quả tối đa"),
    session: Session = Depends(get_session)
):
    """
    API tìm kiếm địa điểm theo tên hoặc từ khóa (case-insensitive, partial match).
    Sử dụng LLM để extract location từ câu query, sau đó filter theo tags.
    Frontend gọi: GET /api/v1/place/search/by-name?q=ha+long&limit=20
    """
    if not q or len(q.strip()) < 2:
        return []
    
    # Dùng LLM để extract location và các thông tin khác
    extraction = await extract_with_groq(q)
    
    # Lấy locations từ LLM extraction
    locations = extraction.location if extraction.location else []
    place_type = extraction.type if extraction.type and extraction.type != "unknown" else None
    
    # Nếu LLM extract được location, filter theo tags
    if locations:
        conditions = []
        for loc in locations:
            # Bỏ dấu để match với tags trong DB (không dấu)
            loc_no_accent = remove_accents(loc)
            search_term = f"%{loc_no_accent}%"
            # Tìm trong tags (chứa tên tỉnh) - cast sang String type
            conditions.append(Place.tags.cast(String).ilike(search_term))
        
        statement = select(Place).where(or_(*conditions)).limit(limit)
        places = session.exec(statement).all()
    else:
        # Nếu không có location, fallback về tìm kiếm theo keyword
        keywords = extract_keywords(q)
        if not keywords:
            keywords = [q.strip()]
        
        conditions = []
        for keyword in keywords:
            search_term = f"%{keyword}%"
            conditions.append(Place.name.ilike(search_term))
            conditions.append(Place.tags.cast(String).ilike(search_term))
        
        statement = select(Place).where(or_(*conditions)).limit(limit)
        places = session.exec(statement).all()
    
    # Convert to PlaceDetailResponse
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