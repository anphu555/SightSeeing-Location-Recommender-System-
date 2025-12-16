from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.schemas import Like, User, Place, Comment
from app.database import get_session
from app.routers.auth import get_current_user
from app.services.scoring_service import RatingScorer
from pydantic import BaseModel

router = APIRouter()

class LikeCommentRequest(BaseModel):
    comment_id: int
    is_like: bool  # True=Like, False=Dislike

class LikePlaceRequest(BaseModel):
    place_id: int
    is_like: bool  # True=Like, False=Dislike

class LikeResponse(BaseModel):
    id: int
    user_id: int
    comment_id: int | None
    place_id: int | None
    created_at: datetime

class LikedCommentResponse(BaseModel):
    id: int
    comment_id: int
    comment_content: str
    comment_user_id: int  # ID của user đã tạo comment
    comment_username: str  # Username của user đã tạo comment
    comment_user_display_name: str | None  # Display name của user đã tạo comment
    comment_user_avatar_url: str | None  # Avatar URL của user đã tạo comment
    place_id: int
    place_name: str
    place_image: str | None
    created_at: datetime

class LikedPlaceResponse(BaseModel):
    id: int
    place_id: int
    place_name: str
    place_image: str | None
    place_province: str | None
    created_at: datetime

# ==========================================
# LIKE/DISLIKE COMMENT
# ==========================================
@router.post("/likes/comment")
async def like_dislike_comment(
    like_data: LikeCommentRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Like hoặc Dislike một comment. 
    Nếu đã like/dislike trước đó với cùng giá trị is_like -> xóa (toggle off)
    Nếu đã like/dislike trước đó với khác is_like -> update (switch giữa like và dislike)"""
    
    # Kiểm tra comment có tồn tại không
    comment = session.get(Comment, like_data.comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Kiểm tra đã có interaction chưa
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.comment_id == like_data.comment_id
    )
    existing_like = session.exec(statement).first()
    
    if existing_like:
        # Nếu đã có và cùng loại (like->like hoặc dislike->dislike) -> xóa (toggle off)
        if existing_like.is_like == like_data.is_like:
            session.delete(existing_like)
            session.commit()
            return {"action": "removed", "status": "neutral"}
        else:
            # Nếu khác loại (like->dislike hoặc dislike->like) -> update
            existing_like.is_like = like_data.is_like
            session.add(existing_like)
            session.commit()
            session.refresh(existing_like)
            
            return {
                "action": "updated",
                "status": "liked" if existing_like.is_like else "disliked",
                "data": {
                    "id": existing_like.id,
                    "user_id": existing_like.user_id,
                    "comment_id": existing_like.comment_id,
                    "place_id": None,
                    "created_at": existing_like.created_at.isoformat()
                }
            }
    
    # Tạo like/dislike mới
    new_like = Like(
        user_id=current_user.id,
        comment_id=like_data.comment_id,
        is_like=like_data.is_like
    )
    
    session.add(new_like)
    session.commit()
    session.refresh(new_like)
    
    return {
        "action": "created",
        "status": "liked" if new_like.is_like else "disliked",
        "data": {
            "id": new_like.id,
            "user_id": new_like.user_id,
            "comment_id": new_like.comment_id,
            "place_id": None,
            "created_at": new_like.created_at.isoformat()
        }
    }

# ==========================================
# UNLIKE COMMENT (DEPRECATED - use POST with same is_like to toggle)
# ==========================================
@router.delete("/likes/comment/{comment_id}")
async def unlike_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """[DEPRECATED] Unlike một comment - Sử dụng POST /likes/comment với cùng is_like để toggle"""
    
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.comment_id == comment_id
    )
    like = session.exec(statement).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    session.delete(like)
    session.commit()
    
    return {"message": "Unliked successfully"}

# ==========================================
# LIKE/DISLIKE PLACE
# ==========================================
@router.post("/likes/place")
async def like_dislike_place(
    like_data: LikePlaceRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Like hoặc Dislike một place.
    Nếu đã like/dislike trước đó với cùng giá trị is_like -> xóa (toggle off)
    Nếu đã like/dislike trước đó với khác is_like -> update (switch giữa like và dislike)
    
    Tự động cập nhật rating score theo thuật toán:
    - Like: +4 điểm
    - Dislike: -5 điểm hoặc điểm tối thiểu 1
    """
    
    # Kiểm tra place có tồn tại không
    place = session.get(Place, like_data.place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    # Kiểm tra đã có interaction chưa
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.place_id == like_data.place_id
    )
    existing_like = session.exec(statement).first()
    
    action = None
    status_str = None
    
    if existing_like:
        # Nếu đã có và cùng loại (like->like hoặc dislike->dislike) -> xóa (toggle off)
        if existing_like.is_like == like_data.is_like:
            session.delete(existing_like)
            session.commit()
            action = "removed"
            status_str = "neutral"
            # Note: We don't update rating when removing like/dislike
        else:
            # Nếu khác loại (like->dislike hoặc dislike->like) -> update
            existing_like.is_like = like_data.is_like
            session.add(existing_like)
            session.commit()
            session.refresh(existing_like)
            
            # Update rating score
            RatingScorer.update_rating(
                user_id=current_user.id,
                place_id=like_data.place_id,
                session=session,
                is_like=like_data.is_like
            )
            
            action = "updated"
            status_str = "liked" if existing_like.is_like else "disliked"
    else:
        # Tạo like/dislike mới
        new_like = Like(
            user_id=current_user.id,
            place_id=like_data.place_id,
            is_like=like_data.is_like
        )
        
        session.add(new_like)
        session.commit()
        session.refresh(new_like)
        
        # Update rating score
        RatingScorer.update_rating(
            user_id=current_user.id,
            place_id=like_data.place_id,
            session=session,
            is_like=like_data.is_like
        )
        
        action = "created"
        status_str = "liked" if new_like.is_like else "disliked"
        existing_like = new_like
    
    if action in ["created", "updated"]:
        return {
            "action": action,
            "status": status_str,
            "data": {
                "id": existing_like.id,
                "user_id": existing_like.user_id,
                "comment_id": None,
                "place_id": existing_like.place_id,
                "created_at": existing_like.created_at.isoformat()
            }
        }
    else:
        return {"action": action, "status": status_str}

# ==========================================
# UNLIKE PLACE (DEPRECATED - use POST with same is_like to toggle)
# ==========================================
@router.delete("/likes/place/{place_id}")
async def unlike_place(
    place_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """[DEPRECATED] Unlike một place - Sử dụng POST /likes/place với cùng is_like để toggle"""
    
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.place_id == place_id
    )
    like = session.exec(statement).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    session.delete(like)
    session.commit()
    
    return {"message": "Unliked successfully"}

# ==========================================
# GET LIKED COMMENTS
# ==========================================
@router.get("/likes/comments", response_model=List[LikedCommentResponse])
async def get_liked_comments(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Lấy danh sách comments mà user đã like"""
    
    statement = (
        select(Like)
        .where(Like.user_id == current_user.id)
        .where(Like.comment_id.isnot(None))
        .where(Like.is_like == True)  # Chỉ lấy likes, không lấy dislikes
        .order_by(Like.created_at.desc())
    )
    
    likes = session.exec(statement).all()
    
    result = []
    for like in likes:
        comment = session.get(Comment, like.comment_id)
        if comment:
            # Lấy thông tin user đã tạo comment
            comment_user = session.get(User, comment.user_id)
            
            place = session.get(Place, comment.place_id)
            place_name = place.name if place else "Unknown Place"
            place_image = place.image[0] if place and place.image and len(place.image) > 0 else None
            
            result.append(LikedCommentResponse(
                id=like.id,
                comment_id=comment.id,
                comment_content=comment.content,
                comment_user_id=comment.user_id,
                comment_username=comment_user.username if comment_user else "Unknown",
                comment_user_display_name=comment_user.display_name if comment_user else None,
                comment_user_avatar_url=comment_user.avatar_url if comment_user else None,
                place_id=comment.place_id,
                place_name=place_name,
                place_image=place_image,
                created_at=like.created_at
            ))
    
    return result

# ==========================================
# GET LIKED PLACES
# ==========================================
@router.get("/likes/places", response_model=List[LikedPlaceResponse])
async def get_liked_places(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Lấy danh sách places mà user đã like"""
    
    statement = (
        select(Like)
        .where(Like.user_id == current_user.id)
        .where(Like.place_id.isnot(None))
        .where(Like.is_like == True)  # Chỉ lấy likes, không lấy dislikes
        .order_by(Like.created_at.desc())
    )
    
    likes = session.exec(statement).all()
    
    result = []
    for like in likes:
        place = session.get(Place, like.place_id)
        if place:
            place_image = place.image[0] if place.image and len(place.image) > 0 else None
            # Get province from tags or description
            place_province = None
            if place.tags and len(place.tags) > 0:
                place_province = place.tags[0]
            
            result.append(LikedPlaceResponse(
                id=like.id,
                place_id=place.id,
                place_name=place.name,
                place_image=place_image,
                place_province=place_province,
                created_at=like.created_at
            ))
    
    return result

# ==========================================
# CHECK IF USER LIKED/DISLIKED
# ==========================================
@router.get("/likes/check/comment/{comment_id}")
async def check_comment_liked(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Kiểm tra user đã like/dislike comment chưa"""
    
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.comment_id == comment_id
    )
    like = session.exec(statement).first()
    
    if like:
        return {"liked": like.is_like, "disliked": not like.is_like, "status": "liked" if like.is_like else "disliked"}
    else:
        return {"liked": False, "disliked": False, "status": "neutral"}

@router.get("/likes/check/place/{place_id}")
async def check_place_liked(
    place_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Kiểm tra user đã like/dislike place chưa"""
    
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.place_id == place_id
    )
    like = session.exec(statement).first()
    
    if like:
        return {"liked": like.is_like, "disliked": not like.is_like, "status": "liked" if like.is_like else "disliked"}
    else:
        return {"liked": False, "disliked": False, "status": "neutral"}
