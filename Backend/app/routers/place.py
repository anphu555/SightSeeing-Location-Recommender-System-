from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import Place, PlaceDetailResponse
from typing import List

router = APIRouter()

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
    
    # Trả về dữ liệu
    return place

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
    
    results = session.exec(statement).all()
    
    return results