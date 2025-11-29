from fastapi import APIRouter, Depends, HTTPException
from app.schemas import RatingCreate, PreferenceEnum
from app.services.db_service import add_user_rating
from app.routers.auth import get_current_user # Import hàm bảo vệ vừa viết
from app.services.db_service import get_user_ratings_map # đổi sang like dislike ok thì xoá cái này

router = APIRouter()

@router.post("/rate")
def submit_rating(rating_data: RatingCreate, username: str = Depends(get_current_user)):
    # Quy đổi: like -> 1, dislike -> -1, none -> 0
    if rating_data.preference == PreferenceEnum.like:
        score_value = 1
    elif rating_data.preference == PreferenceEnum.dislike:
        score_value = -1
    else:  # none
        score_value = 0
    
    success = add_user_rating(username, rating_data.place_id, score_value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save interaction")
    
    return {"message": f"{rating_data.preference.value} saved successfully", "place_id": rating_data.place_id, "score": score_value}

@router.get("/my-ratings")
def get_my_ratings(username: str = Depends(get_current_user)):
    # Trả về: { "101": 1, "102": -1 }
    return get_user_ratings_map(username)