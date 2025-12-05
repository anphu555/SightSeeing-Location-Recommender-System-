from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.database import get_session
from app.schemas import Place, PlaceDetailResponse

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