from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import InteractionCreate, InteractionType, Rating, User
from app.routers.auth import get_current_user

router = APIRouter()

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