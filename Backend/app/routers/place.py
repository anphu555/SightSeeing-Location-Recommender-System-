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
from typing import List, Optional
import math

router = APIRouter()

# === HELPER FUNCTION: Tính khoảng cách Haversine ===
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách giữa 2 điểm địa lý bằng công thức Haversine.
    Trả về khoảng cách tính bằng km.
    """
    R = 6371  # Bán kính Trái Đất (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon / 2) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

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
    
    # Trả về dữ liệu với province và climate
    return PlaceDetailResponse(
        id=place.id,
        name=place.name,
        description=place.description,
        image=place.image,
        tags=place.tags,
        province=province,
        climate=place.climate,
        lat=place.lat,
        lon=place.lon
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
    
    # Convert to PlaceDetailResponse with province and climate
    results = []
    for place in places:
        province = place.tags[0] if place.tags and len(place.tags) > 0 else None
        results.append(PlaceDetailResponse(
            id=place.id,
            name=place.name,
            description=place.description,
            image=place.image,
            tags=place.tags,
            province=province,
            climate=place.climate,
            lat=place.lat,
            lon=place.lon
        ))
    
    return results


# === RESPONSE MODEL CHO NEARBY API (bao gồm distance) ===
from pydantic import BaseModel

class PlaceWithDistance(BaseModel):
    id: int
    name: str
    description: List[str]
    image: List[str]
    tags: List[str]
    province: Optional[str] = None
    climate: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance: Optional[float] = None  # Khoảng cách tính bằng km


@router.get("/search/nearby", response_model=List[PlaceWithDistance])
def search_nearby_places(
    lat: float = Query(..., description="Vĩ độ người dùng"),
    lon: float = Query(..., description="Kinh độ người dùng"),
    limit: int = Query(50, ge=1, le=200, description="Số lượng kết quả tối đa"),
    max_distance: float = Query(500.0, description="Khoảng cách tối đa (km)"),
    session: Session = Depends(get_session)
):
    """
    API tìm kiếm địa điểm gần vị trí người dùng và sắp xếp theo khoảng cách.
    Frontend gọi: GET /api/v1/place/search/nearby?lat=10.762&lon=106.660&limit=50&max_distance=500
    """
    # Lấy tất cả places có lat/lon
    statement = select(Place).where(
        Place.lat.isnot(None),
        Place.lon.isnot(None)
    )
    
    places = session.exec(statement).all()
    
    # Tính khoảng cách và lọc theo max_distance
    places_with_distance = []
    for place in places:
        if place.lat is not None and place.lon is not None:
            distance = calculate_distance(lat, lon, place.lat, place.lon)
            
            if distance <= max_distance:
                province = place.tags[0] if place.tags and len(place.tags) > 0 else None
                places_with_distance.append(PlaceWithDistance(
                    id=place.id,
                    name=place.name,
                    description=place.description,
                    image=place.image,
                    tags=place.tags,
                    province=province,
                    climate=place.climate,
                    lat=place.lat,
                    lon=place.lon,
                    distance=round(distance, 2)
                ))
    
    # Sắp xếp theo khoảng cách tăng dần
    places_with_distance.sort(key=lambda x: x.distance if x.distance is not None else float('inf'))
    
    # Giới hạn số lượng kết quả
    return places_with_distance[:limit]