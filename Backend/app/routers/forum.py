"""
Forum/Post Router - API cho chức năng đăng bài review địa điểm
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select, desc
from typing import List, Optional
from datetime import datetime
import os
import uuid

from app.database import get_session
from app.schemas import (
    Post, PostLike, PostComment, User, Place,
    PostCreate, PostCommentCreate,
    PostResponse, PostCommentResponse, PostUserInfo, PostPlaceInfo
)
from app.routers.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/v1/forum", tags=["Forum"])

# Thư mục lưu ảnh posts
UPLOAD_DIR = "uploads/posts"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_post_response(post: Post, session: Session, current_user_id: Optional[int] = None) -> PostResponse:
    """Convert Post model to PostResponse với đầy đủ thông tin"""
    
    # Lấy thông tin user
    user = session.get(User, post.user_id)
    user_info = PostUserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url
    ) if user else None
    
    # Lấy thông tin place nếu có
    place_info = None
    if post.place_id:
        place = session.get(Place, post.place_id)
        if place:
            place_info = PostPlaceInfo(
                id=place.id,
                name=place.name,
                image=place.image[0] if place.image else None
            )
    
    # Kiểm tra user hiện tại đã like chưa
    is_liked = False
    if current_user_id:
        like = session.exec(
            select(PostLike).where(
                PostLike.post_id == post.id,
                PostLike.user_id == current_user_id
            )
        ).first()
        is_liked = like is not None
    
    # Lấy 3 comments gần nhất
    comments_query = select(PostComment).where(
        PostComment.post_id == post.id
    ).order_by(desc(PostComment.created_at)).limit(3)
    comments = session.exec(comments_query).all()
    
    comments_response = []
    for comment in comments:
        comment_user = session.get(User, comment.user_id)
        comments_response.append(PostCommentResponse(
            id=comment.id,
            content=comment.content,
            created_at=comment.created_at,
            user=PostUserInfo(
                id=comment_user.id,
                username=comment_user.username,
                display_name=comment_user.display_name,
                avatar_url=comment_user.avatar_url
            ) if comment_user else None
        ))
    
    return PostResponse(
        id=post.id,
        content=post.content,
        images=post.images or [],
        created_at=post.created_at,
        like_count=post.like_count,
        comment_count=post.comment_count,
        user=user_info,
        place=place_info,
        is_liked=is_liked,
        comments=comments_response
    )


# ============ POSTS CRUD ============

@router.get("/posts", response_model=List[PostResponse])
def get_posts(
    skip: int = 0,
    limit: int = 20,
    place_id: Optional[int] = None,
    user_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Lấy danh sách posts (feed)"""
    query = select(Post).order_by(desc(Post.created_at))
    
    if place_id:
        query = query.where(Post.place_id == place_id)
    if user_id:
        query = query.where(Post.user_id == user_id)
    
    query = query.offset(skip).limit(limit)
    posts = session.exec(query).all()
    
    current_user_id = current_user.id if current_user else None
    return [get_post_response(post, session, current_user_id) for post in posts]


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Lấy chi tiết một post"""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    current_user_id = current_user.id if current_user else None
    return get_post_response(post, session, current_user_id)


@router.post("/posts", response_model=PostResponse)
def create_post(
    post_data: PostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Tạo bài post mới"""
    # Validate place_id nếu có
    if post_data.place_id:
        place = session.get(Place, post_data.place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
    
    # Tạo post
    post = Post(
        user_id=current_user.id,
        place_id=post_data.place_id,
        content=post_data.content,
        images=post_data.images,
        created_at=datetime.utcnow()
    )
    
    session.add(post)
    session.commit()
    session.refresh(post)
    
    return get_post_response(post, session, current_user.id)


@router.post("/posts/{post_id}/images")
async def upload_post_images(
    post_id: int,
    files: List[UploadFile] = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Upload ảnh cho post"""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    uploaded_urls = []
    for file in files:
        # Tạo filename unique
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Lưu file
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        uploaded_urls.append(f"/uploads/posts/{filename}")
    
    # Cập nhật post
    post.images = (post.images or []) + uploaded_urls
    session.add(post)
    session.commit()
    
    return {"urls": uploaded_urls}


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Xóa post"""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Xóa likes và comments liên quan
    session.exec(select(PostLike).where(PostLike.post_id == post_id)).all()
    for like in session.exec(select(PostLike).where(PostLike.post_id == post_id)).all():
        session.delete(like)
    
    for comment in session.exec(select(PostComment).where(PostComment.post_id == post_id)).all():
        session.delete(comment)
    
    session.delete(post)
    session.commit()
    
    return {"message": "Post deleted"}


# ============ LIKES ============

@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Toggle like/unlike post"""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Kiểm tra đã like chưa
    existing_like = session.exec(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id
        )
    ).first()
    
    if existing_like:
        # Unlike
        session.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        action = "unliked"
    else:
        # Like
        new_like = PostLike(
            user_id=current_user.id,
            post_id=post_id,
            created_at=datetime.utcnow()
        )
        session.add(new_like)
        post.like_count += 1
        action = "liked"
    
    session.add(post)
    session.commit()
    
    return {"action": action, "like_count": post.like_count}


# ============ COMMENTS ============

@router.get("/posts/{post_id}/comments", response_model=List[PostCommentResponse])
def get_comments(
    post_id: int,
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session)
):
    """Lấy danh sách comments của post"""
    query = select(PostComment).where(
        PostComment.post_id == post_id
    ).order_by(desc(PostComment.created_at)).offset(skip).limit(limit)
    
    comments = session.exec(query).all()
    
    result = []
    for comment in comments:
        user = session.get(User, comment.user_id)
        result.append(PostCommentResponse(
            id=comment.id,
            content=comment.content,
            created_at=comment.created_at,
            user=PostUserInfo(
                id=user.id,
                username=user.username,
                display_name=user.display_name,
                avatar_url=user.avatar_url
            ) if user else None
        ))
    
    return result


@router.post("/posts/{post_id}/comments", response_model=PostCommentResponse)
def create_comment(
    post_id: int,
    comment_data: PostCommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Tạo comment mới"""
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = PostComment(
        user_id=current_user.id,
        post_id=post_id,
        content=comment_data.content,
        created_at=datetime.utcnow()
    )
    
    session.add(comment)
    
    # Cập nhật comment count
    post.comment_count += 1
    session.add(post)
    
    session.commit()
    session.refresh(comment)
    
    return PostCommentResponse(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at,
        user=PostUserInfo(
            id=current_user.id,
            username=current_user.username,
            display_name=current_user.display_name,
            avatar_url=current_user.avatar_url
        )
    )


@router.delete("/posts/{post_id}/comments/{comment_id}")
def delete_comment(
    post_id: int,
    comment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Xóa comment"""
    comment = session.get(PostComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    post = session.get(Post, post_id)
    if post:
        post.comment_count = max(0, post.comment_count - 1)
        session.add(post)
    
    session.delete(comment)
    session.commit()
    
    return {"message": "Comment deleted"}


# ============ UPLOAD IMAGES (pre-upload before creating post) ============

@router.post("/upload")
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload ảnh trước khi tạo post (pre-upload)"""
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed")
    
    uploaded_urls = []
    for file in files:
        # Validate file type
        if not file.content_type.startswith("image/"):
            continue
            
        # Tạo filename unique
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Lưu file
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        uploaded_urls.append(f"/uploads/posts/{filename}")
    
    return {"urls": uploaded_urls}


# ============ FEED ============

@router.get("/feed", response_model=List[PostResponse])
def get_feed(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Lấy feed posts (alias của /posts)"""
    query = select(Post).order_by(desc(Post.created_at)).offset(skip).limit(limit)
    posts = session.exec(query).all()
    
    current_user_id = current_user.id if current_user else None
    return [get_post_response(post, session, current_user_id) for post in posts]


# ============ LIKED POSTS ============

@router.get("/likes/posts", response_model=List[PostResponse])
def get_liked_posts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách posts mà user đã like"""
    # Lấy danh sách post_id từ PostLike
    liked_posts_query = select(PostLike).where(
        PostLike.user_id == current_user.id
    ).order_by(desc(PostLike.created_at))
    
    liked_posts = session.exec(liked_posts_query).all()
    
    # Lấy thông tin chi tiết các posts
    result = []
    for like in liked_posts:
        post = session.get(Post, like.post_id)
        if post:
            result.append(get_post_response(post, session, current_user.id))
    
    return result
