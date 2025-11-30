from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_user
from app.schemas import Rating, RatingCreate, InteractionType, User
from app.database import get_session

router = APIRouter()

# Cấu hình điểm số cho từng loại interaction
INTERACTION_WEIGHTS = {
    InteractionType.like: 2.0,      # +2.0 điểm
    InteractionType.dislike: -2.0,  # -2.0 điểm
    InteractionType.click: 0.3,     # +0.3 điểm
    InteractionType.view: 0.5,      # +0.5 điểm (view >30s)
    InteractionType.none: 0.0,      # +0.0 điểm
}

@router.post("/rate")
def submit_rating(
    rating_data: RatingCreate, 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Tích lũy score từ các interactions:
    - like: +2.0
    - dislike: -2.0
    - click: +0.3
    - view (>30s): +0.5
    - none: +0.0
    
    Score sẽ được giới hạn trong khoảng [1.0, 5.0]
    """
    # Kiểm tra xem user đã rate địa điểm này chưa
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == rating_data.place_id
    )
    existing_rating = session.exec(statement).first()
    
    # Lấy weight của interaction type
    weight = INTERACTION_WEIGHTS.get(rating_data.interaction_type, 0.0)
    
    if existing_rating:
        # Tích lũy score (cộng dồn)
        new_score = existing_rating.score + weight
        # Giới hạn trong khoảng [1.0, 5.0]
        existing_rating.score = max(1.0, min(5.0, new_score))
        session.add(existing_rating)
        final_score = existing_rating.score
    else:
        # Tạo rating mới với score khởi đầu = 3.0 + weight
        initial_score = 3.0 + weight
        final_score = max(1.0, min(5.0, initial_score))
        new_rating = Rating(
            user_id=current_user.id,
            place_id=rating_data.place_id,
            score=final_score
        )
        session.add(new_rating)
    
    session.commit()
    
    return {
        "message": f"{rating_data.interaction_type.value} saved successfully", 
        "place_id": rating_data.place_id, 
        "score": round(final_score, 2),
        "interaction_type": rating_data.interaction_type.value
    }

@router.get("/my-ratings")
def get_my_ratings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Lấy tất cả ratings của user hiện tại
    Returns: { place_id: score }
    """
    statement = select(Rating).where(Rating.user_id == current_user.id)
    ratings = session.exec(statement).all()
    
    # Chuyển đổi thành dictionary: { place_id: score }
    result = {rating.place_id: round(rating.score, 2) for rating in ratings}
    return result