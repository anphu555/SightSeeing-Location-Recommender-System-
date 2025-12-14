from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import Place, PlaceDetailResponse, PlaceWithDistance
from typing import List
from math import radians, cos, sin, asin, sqrt

router = APIRouter()

# === HAVERSINE DISTANCE CALCULATION ===
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách giữa 2 điểm GPS trên Trái Đất (đơn vị: km)
    Sử dụng công thức Haversine
    """
    # Chuyển đổi từ độ sang radian
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Hiệu số
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Công thức Haversine
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Bán kính Trái Đất = 6371 km
    km = 6371 * c
    return round(km, 2)

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

@router.get("/search/nearby", response_model=List[PlaceWithDistance])
def search_nearby_places(
    lat: float = Query(..., description="Latitude của người dùng"),
    lon: float = Query(..., description="Longitude của người dùng"),
    limit: int = Query(50, ge=1, le=200, description="Số lượng kết quả tối đa"),
    max_distance: float = Query(500, description="Bán kính tìm kiếm (km)"),
    session: Session = Depends(get_session)
):
    """
    API tìm kiếm các địa điểm gần người dùng, sắp xếp theo khoảng cách.
    Frontend gọi: GET /api/v1/place/search/nearby?lat=21.0285&lon=105.8542&limit=50
    
    Returns: Danh sách địa điểm có kèm theo khoảng cách (km)
    """
    # Lấy tất cả địa điểm có tọa độ GPS
    statement = select(Place).where(
        Place.latitude.isnot(None),
        Place.longitude.isnot(None)
    )
    places = session.exec(statement).all()
    
    # Tính khoảng cách cho từng địa điểm
    places_with_distance = []
    for place in places:
        distance = haversine_distance(lat, lon, place.latitude, place.longitude)
        
        # Chỉ lấy địa điểm trong phạm vi max_distance
        if distance <= max_distance:
            province = place.tags[0] if place.tags and len(place.tags) > 0 else None
            
            places_with_distance.append(PlaceWithDistance(
                id=place.id,
                name=place.name,
                description=place.description,
                image=place.image,
                tags=place.tags,
                province=province,
                distance=distance,
                latitude=place.latitude,
                longitude=place.longitude
            ))
    
    # Sắp xếp theo khoảng cách (gần nhất trước)
    places_with_distance.sort(key=lambda x: x.distance)
    
    # Giới hạn số lượng kết quả
    return places_with_distance[:limit]