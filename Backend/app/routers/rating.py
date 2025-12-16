from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import InteractionCreate, InteractionType, Rating, User
from app.routers.auth import get_current_user
from app.services.scoring_service import RatingScorer
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class ViewTimeRequest(BaseModel):
    """Request model for tracking view time"""
    place_id: int
    view_time_seconds: float
    raw_view_time: Optional[float] = None  # Original view time before engagement adjustment
    scroll_depth: Optional[int] = None  # Scroll depth percentage (0-100)
    has_interacted: Optional[bool] = None  # Whether user interacted (scroll, click, etc.)

class RatingResponse(BaseModel):
    """Response model for rating operations"""
    user_id: int
    place_id: int
    score: float
    status: str  # "created" or "updated"

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/view-time", response_model=RatingResponse)
async def track_view_time(
    view_data: ViewTimeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Track user view time on a place and calculate rating score.
    Includes engagement metrics (scroll depth, interactions).
    """
    # Log engagement metrics for monitoring
    print(f"[View Time Tracking] User {current_user.id} - Place {view_data.place_id}:")
    print(f"  - Adjusted view time: {view_data.view_time_seconds}s")
    if view_data.raw_view_time:
        print(f"  - Raw view time: {view_data.raw_view_time}s")
    if view_data.scroll_depth is not None:
        print(f"  - Scroll depth: {view_data.scroll_depth}%")
    if view_data.has_interacted is not None:
        print(f"  - Has interacted: {view_data.has_interacted}")
    
    # Update rating using the scoring algorithm (uses adjusted view time)
    rating = RatingScorer.update_rating(
        user_id=current_user.id,
        place_id=view_data.place_id,
        session=session,
        view_time_seconds=view_data.view_time_seconds
    )
    
    # Check if it was newly created or updated
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == view_data.place_id
    )
    existing_count = len(session.exec(statement).all())
    
    return RatingResponse(
        user_id=rating.user_id,
        place_id=rating.place_id,
        score=rating.score,
        status="created" if existing_count == 1 else "updated"
    )

@router.get("/rating/{place_id}")
async def get_user_rating(
    place_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user's rating for a specific place"""
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == place_id
    )
    rating = session.exec(statement).first()
    
    if not rating:
        return {"place_id": place_id, "score": None, "message": "No rating found"}
    
    return {
        "place_id": rating.place_id,
        "score": rating.score,
        "user_id": rating.user_id
    }

# ==========================================
# LEGACY ENDPOINTS (Keep for backward compatibility)
# ==========================================

# Quy tắc tính điểm
SCORE_MAP = {
    InteractionType.like: 5.0,
    InteractionType.view: 3.0,  # Xem > 30s
    InteractionType.click: 1.0, # Click xem
    InteractionType.dislike: -1.0
}

@router.post("/interact")
async def track_interaction(
    interaction: InteractionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    API này được gọi ngầm (background) khi user tương tác với UI.
    Nó cập nhật điểm số (Implicit Feedback) để dùng cho lần gợi ý sau.
    """
    
    # 1. Kiểm tra rating cũ
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == interaction.place_id
    )
    existing_rating = session.exec(statement).first()
    
    # 2. Lấy điểm số tương ứng hành vi mới
    new_score = SCORE_MAP.get(interaction.interaction_type, 1.0)

    if existing_rating:
        # LOGIC: Chỉ update nếu hành vi mới có trọng số cao hơn (Vd: đã Click(1) giờ Like(5) -> Lên 5)
        # Hoặc nếu là dislike thì update ngay để loại bỏ
        if interaction.interaction_type == InteractionType.dislike:
            existing_rating.score = -1.0 # Đánh dấu tiêu cực
        elif new_score > existing_rating.score:
            existing_rating.score = new_score
        
        session.add(existing_rating)
        session.commit()
        return {"status": "updated", "score": existing_rating.score}

    else:
        # Tạo rating mới
        new_rating = Rating(
            user_id=current_user.id,
            place_id=interaction.place_id,
            score=new_score
        )
        session.add(new_rating)
        session.commit()
        return {"status": "created", "score": new_score}