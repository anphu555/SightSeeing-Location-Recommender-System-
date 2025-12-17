from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import Place, PlaceDetailResponse
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
def search_places_by_name(
    q: str = Query(..., description="Tên địa điểm cần tìm"),
    limit: int = Query(50, ge=1, le=100, description="Số lượng kết quả tối đa"),
    session: Session = Depends(get_session)
):
    """
    API tìm kiếm địa điểm theo tên (case-insensitive, partial match).
    Frontend gọi: GET /api/v1/place/search/by-name?q=ha+long&limit=20
    """
    if not q or len(q.strip()) < 2:
        return []
    
    # Tìm kiếm không phân biệt hoa thường, cho phép match một phần
    search_term = f"%{q.lower()}%"
    
    statement = select(Place).where(
        Place.name.ilike(search_term)
    ).limit(limit)
    
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