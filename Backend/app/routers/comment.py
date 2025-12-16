from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from app.schemas import Comment, User, Place
from app.database import get_session
from app.routers.auth import get_current_user
from app.services.scoring_service import RatingScorer
from pydantic import BaseModel

router = APIRouter()

class CommentCreate(BaseModel):
    place_id: int
    content: str

class CommentResponse(BaseModel):
    id: int
    user_id: int
    username: str
    user_display_name: str | None = None  # Tên hiển thị của user
    user_avatar_url: str | None = None  # Avatar URL của user
    place_id: int
    place_name: str | None = None
    place_image: str | None = None
    content: str
    created_at: datetime

@router.post("/comments", response_model=CommentResponse)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Tạo comment mới cho địa điểm và tự động cập nhật rating score (+0.5 cho comment đầu tiên)"""
    
    # Kiểm tra place có tồn tại không
    place = session.get(Place, comment_data.place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    # Tạo comment
    new_comment = Comment(
        user_id=current_user.id,
        place_id=comment_data.place_id,
        content=comment_data.content
    )
    
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    
    # Update rating score (only +0.5 for first comment)
    RatingScorer.update_rating(
        user_id=current_user.id,
        place_id=comment_data.place_id,
        session=session,
        has_commented=True
    )
    
    return CommentResponse(
        id=new_comment.id,
        user_id=new_comment.user_id,
        username=current_user.username,
        user_display_name=current_user.display_name,
        user_avatar_url=current_user.avatar_url,
        place_id=new_comment.place_id,
        content=new_comment.content,
        created_at=new_comment.created_at
    )

@router.get("/comments/place/{place_id}", response_model=List[CommentResponse])
async def get_comments_by_place(
    place_id: int,
    session: Session = Depends(get_session)
):
    """Lấy tất cả comments của một địa điểm"""
    
    statement = (
        select(Comment, User)
        .join(User)
        .where(Comment.place_id == place_id)
        .order_by(Comment.created_at.desc())
    )
    
    results = session.exec(statement).all()
    
    comments = []
    for comment, user in results:
        comments.append(CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            username=user.username,
            user_display_name=user.display_name,
            user_avatar_url=user.avatar_url,
            place_id=comment.place_id,
            content=comment.content,
            created_at=comment.created_at
        ))
    
    return comments

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Xóa comment (chỉ người tạo mới xóa được)"""
    
    comment = session.get(Comment, comment_id)
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    session.delete(comment)
    session.commit()
    
    return {"message": "Comment deleted successfully"}

@router.get("/comments/user", response_model=List[CommentResponse])
async def get_comments_by_user(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Lấy tất cả comments của user hiện tại"""
    
    statement = (
        select(Comment)
        .where(Comment.user_id == current_user.id)
        .order_by(Comment.created_at.desc())
    )
    
    results = session.exec(statement).all()
    
    comments = []
    for comment in results:
        # Fetch place info
        place = session.get(Place, comment.place_id)
        place_name = place.name if place else "Unknown Place"
        place_image = place.image[0] if place and place.image and len(place.image) > 0 else None
        
        comments.append(CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            username=current_user.username,
            user_display_name=current_user.display_name,
            user_avatar_url=current_user.avatar_url,
            place_id=comment.place_id,
            place_name=place_name,
            place_image=place_image,
            content=comment.content,
            created_at=comment.created_at
        ))
    
    return comments
