from fastapi import APIRouter, Depends, HTTPException
from app.schemas import RatingCreate
from app.services.db_service import add_user_rating
from app.routers.auth import get_current_user # Import hàm bảo vệ vừa viết

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