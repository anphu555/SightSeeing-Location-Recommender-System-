from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.schemas import Like, User, Place, Comment
from app.database import get_session
from app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class LikeCommentRequest(BaseModel):
    comment_id: int

class LikePlaceRequest(BaseModel):
    place_id: int

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
# LIKE COMMENT
# ==========================================
@router.post("/likes/comment", response_model=LikeResponse)
async def like_comment(
    like_data: LikeCommentRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Like một comment"""
    
    # Kiểm tra comment có tồn tại không
    comment = session.get(Comment, like_data.comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Kiểm tra đã like chưa
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.comment_id == like_data.comment_id
    )
    existing_like = session.exec(statement).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked this comment")
    
    # Tạo like mới
    new_like = Like(
        user_id=current_user.id,
        comment_id=like_data.comment_id
    )
    
    session.add(new_like)
    session.commit()
    session.refresh(new_like)
    
    return LikeResponse(
        id=new_like.id,
        user_id=new_like.user_id,
        comment_id=new_like.comment_id,
        place_id=None,
        created_at=new_like.created_at
    )

# ==========================================
# UNLIKE COMMENT
# ==========================================
@router.delete("/likes/comment/{comment_id}")
async def unlike_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Unlike một comment"""
    
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
# LIKE PLACE
# ==========================================
@router.post("/likes/place", response_model=LikeResponse)
async def like_place(
    like_data: LikePlaceRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Like một place"""
    
    # Kiểm tra place có tồn tại không
    place = session.get(Place, like_data.place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    # Kiểm tra đã like chưa
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.place_id == like_data.place_id
    )
    existing_like = session.exec(statement).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked this place")
    
    # Tạo like mới
    new_like = Like(
        user_id=current_user.id,
        place_id=like_data.place_id
    )
    
    session.add(new_like)
    session.commit()
    session.refresh(new_like)
    
    return LikeResponse(
        id=new_like.id,
        user_id=new_like.user_id,
        comment_id=None,
        place_id=new_like.place_id,
        created_at=new_like.created_at
    )

# ==========================================
# UNLIKE PLACE
# ==========================================
@router.delete("/likes/place/{place_id}")
async def unlike_place(
    place_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Unlike một place"""
    
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
        .order_by(Like.created_at.desc())
    )
    
    likes = session.exec(statement).all()
    
    result = []
    for like in likes:
        comment = session.get(Comment, like.comment_id)
        if comment:
            place = session.get(Place, comment.place_id)
            place_name = place.name if place else "Unknown Place"
            place_image = place.image[0] if place and place.image and len(place.image) > 0 else None
            
            result.append(LikedCommentResponse(
                id=like.id,
                comment_id=comment.id,
                comment_content=comment.content,
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
# CHECK IF USER LIKED
# ==========================================
@router.get("/likes/check/comment/{comment_id}")
async def check_comment_liked(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Kiểm tra user đã like comment chưa"""
    
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.comment_id == comment_id
    )
    like = session.exec(statement).first()
    
    return {"liked": like is not None}

@router.get("/likes/check/place/{place_id}")
async def check_place_liked(
    place_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Kiểm tra user đã like place chưa"""
    
    statement = select(Like).where(
        Like.user_id == current_user.id,
        Like.place_id == place_id
    )
    like = session.exec(statement).first()
    
    return {"liked": like is not None}
