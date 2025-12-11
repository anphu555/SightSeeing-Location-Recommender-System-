from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import InteractionCreate, InteractionType, Rating, User, WatchTimeUpdate
from app.routers.auth import get_current_user
from app.services.scoring_service import (
    update_score_on_search_similarity,
    update_score_on_like,
    update_score_on_dislike,
    update_score_on_watch_time
)

router = APIRouter()

# Quy tắc tính điểm (UPDATED)
# - search_appear: +0.5 per appearance
# - like: set to 10.0 (max)
# - dislike: set to 1.0 (min)
# - watch_time: 
#   * <10s: -2.0
#   * 10-60s: +1.0
#   * >60s: +2.0

@router.post("/interact")
async def track_interaction(
    interaction: InteractionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    API này được gọi ngầm (background) khi user tương tác với UI.
    Nó cập nhật điểm số (Implicit Feedback) để dùng cho lần gợi ý sau.
    
    Supported interactions:
    - search_appear: Place appeared in search with similar themes (+0.5)
    - like: User liked place (score = 10.0)
    - dislike: User disliked place (score = 1.0)
    - watch_time: Time spent viewing (variable score based on duration)
    """
    
    # Validate watch_time interaction
    if interaction.interaction_type == InteractionType.watch_time:
        if interaction.watch_time_seconds is None:
            raise HTTPException(
                status_code=400,
                detail="watch_time_seconds is required for watch_time interaction"
            )
    
    # 1. Kiểm tra rating cũ
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == interaction.place_id
    )
    existing_rating = session.exec(statement).first()
    
    # Get current score or initialize to 0
    current_score = existing_rating.score if existing_rating else 0.0
    
    # 2. Calculate new score based on interaction type
    if interaction.interaction_type == InteractionType.search_appear:
        new_score = update_score_on_search_similarity(current_score)
        
    elif interaction.interaction_type == InteractionType.like:
        new_score = update_score_on_like(current_score)
        
    elif interaction.interaction_type == InteractionType.dislike:
        new_score = update_score_on_dislike(current_score)
        
    elif interaction.interaction_type == InteractionType.watch_time:
        new_score = update_score_on_watch_time(
            current_score, 
            interaction.watch_time_seconds
        )
        
    elif interaction.interaction_type == InteractionType.view:
        # Legacy support - treat as moderate watch time
        new_score = update_score_on_watch_time(current_score, 30)
        
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown interaction type: {interaction.interaction_type}"
        )

    # 3. Update or create rating
    if existing_rating:
        existing_rating.score = new_score
        session.add(existing_rating)
        session.commit()
        session.refresh(existing_rating)
        return {
            "status": "updated",
            "score": existing_rating.score,
            "interaction_type": interaction.interaction_type,
            "previous_score": current_score
        }
    else:
        new_rating = Rating(
            user_id=current_user.id,
            place_id=interaction.place_id,
            score=new_score
        )
        session.add(new_rating)
        session.commit()
        session.refresh(new_rating)
        return {
            "status": "created",
            "score": new_rating.score,
            "interaction_type": interaction.interaction_type,
            "previous_score": 0.0
        }


@router.post("/watch-time")
async def track_watch_time(
    watch_data: WatchTimeUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Dedicated endpoint for tracking watch time.
    This can be called periodically (e.g., every 10 seconds) while user views a place.
    
    Scoring:
    - <10s: -2 points (quick bounce)
    - 10-60s: +1 point (moderate engagement)
    - >60s: +2 points (strong engagement)
    """
    
    # Get or create rating
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == watch_data.place_id
    )
    existing_rating = session.exec(statement).first()
    
    current_score = existing_rating.score if existing_rating else 0.0
    new_score = update_score_on_watch_time(current_score, watch_data.watch_time_seconds)
    
    if existing_rating:
        existing_rating.score = new_score
        session.add(existing_rating)
    else:
        existing_rating = Rating(
            user_id=current_user.id,
            place_id=watch_data.place_id,
            score=new_score
        )
        session.add(existing_rating)
    
    session.commit()
    session.refresh(existing_rating)
    
    return {
        "status": "updated",
        "score": existing_rating.score,
        "watch_time_seconds": watch_data.watch_time_seconds,
        "previous_score": current_score
    }


@router.get("/my-ratings")
async def get_my_ratings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get all ratings for the current user.
    """
    statement = select(Rating).where(Rating.user_id == current_user.id)
    ratings = session.exec(statement).all()
    
    return {
        "user_id": current_user.id,
        "total_ratings": len(ratings),
        "ratings": [
            {
                "place_id": r.place_id,
                "score": r.score
            }
            for r in ratings
        ]
    }


@router.get("/rating/{place_id}")
async def get_rating_for_place(
    place_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get the current user's rating for a specific place.
    """
    statement = select(Rating).where(
        Rating.user_id == current_user.id,
        Rating.place_id == place_id
    )
    rating = session.exec(statement).first()
    
    if not rating:
        return {
            "place_id": place_id,
            "score": None,
            "message": "No rating found"
        }
    
    return {
        "place_id": place_id,
        "score": rating.score
    }