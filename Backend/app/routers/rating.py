from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import InteractionCreate, InteractionType, Rating, User
from app.routers.auth import get_current_user

router = APIRouter()

# Bảng quy đổi điểm số cho hành vi
SCORE_MAP = {
    InteractionType.like: 5.0,
    InteractionType.view: 3.0,  # Xem lâu
    InteractionType.click: 1.0, # Click vào xem
    InteractionType.dislike: -1.0
}

@router.post("/interact")
async def track_interaction(
    interaction: InteractionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    API này nhận hành vi (click, like...) và cập nhật điểm số (score)
    vào bảng Rating để model Two-Tower học.
    """
    
    # 1. Tìm xem user đã từng tương tác với địa điểm này chưa
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == interaction.place_id
    )
    existing_rating = session.exec(statement).first()
    
    new_score = SCORE_MAP.get(interaction.interaction_type, 1.0)

    if existing_rating:
        # LOGIC UPDATE:
        # Nếu hành vi mới có trọng số cao hơn (vd: Like > Click), ta cập nhật điểm lên.
        # Nếu user đã Like (5.0) rồi mà click lại (1.0), ta giữ nguyên 5.0.
        if new_score > existing_rating.score:
            existing_rating.score = new_score
            session.add(existing_rating)
            session.commit()
            return {"status": "updated", "score": new_score}
        
        # Trường hợp đặc biệt: Nếu dislike thì set luôn
        if interaction.interaction_type == InteractionType.dislike:
            existing_rating.score = -1.0 # Hoặc xóa luôn tùy logic
            session.add(existing_rating)
            session.commit()
            return {"status": "disliked"}

        return {"status": "kept_existing", "score": existing_rating.score}

    else:
        # LOGIC CREATE: Chưa tương tác bao giờ -> Tạo mới
        new_rating = Rating(
            user_id=current_user.id,
            place_id=interaction.place_id,
            score=new_score
        )
        session.add(new_rating)
        session.commit()
        return {"status": "created", "score": new_score}