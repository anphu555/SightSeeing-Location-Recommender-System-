from fastapi import APIRouter, Depends, HTTPException
from app.schemas import RatingCreate
from app.services.db_service import add_user_rating
from app.routers.auth import get_current_user # Import hàm bảo vệ vừa viết
from app.services.db_service import add_user_rating, get_user_ratings_map

router = APIRouter()

@router.post("/rate")
def submit_rating(rating_data: RatingCreate, username: str = Depends(get_current_user)):
    """
    API này yêu cầu Header: Authorization: Bearer <token>
    """
    success = add_user_rating(username, rating_data.place_id, rating_data.score)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save rating")
    
    return {"message": "Rating saved successfully", "place_id": rating_data.place_id, "score": rating_data.score}

@router.get("/my-ratings")
def get_my_ratings(username: str = Depends(get_current_user)):
    """
    Trả về danh sách các địa điểm user đã đánh giá.
    Output: { "1": 5, "10": 4 }
    """
    return get_user_ratings_map(username)