from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from pydantic import BaseModel
from enum import Enum

# ==========================================
# DATABASE TABLES (table=True) (create table in db)
# These create the actual rows in your DB.
# ==========================================


# --- ENUMS ---
class InteractionType(str, Enum):
    like = "like"       # User bấm like/tim (trọng số cao nhất)
    dislike = "dislike" # User không thích
    click = "click"     # User bấm vào xem chi tiết (trọng số thấp)
    view = "view"       # User xem lâu (>30s) (trọng số trung bình)

# table = true để tạo bảng cho db (trong file sqlite)
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str  # We store the hash, not the raw password

    # Profile fields
    display_name: Optional[str] = None  # Tên hiển thị, default là username nếu không set
    avatar_url: Optional[str] = None  # URL avatar, None sẽ dùng default avatar
    cover_image_url: Optional[str] = None  # URL ảnh bìa
    bio: Optional[str] = None  # Bio/giới thiệu bản thân
    location: Optional[str] = None  # Vị trí/địa điểm

    # Ví dụ: ["Nature", "Beach", "Food"]
    preferences: List[str] = Field(default=[], sa_column=Column(JSON))

    # Relationships (Optional but recommended)
    ratings: List["Rating"] = Relationship(back_populates="user")

    comments: List["Comment"] = Relationship(back_populates="user")


class Place(SQLModel, table=True):
    # 1. ID: Standard Auto-Incrementing Primary Key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 2. Basic String
    name: str
    
    # 3. List Fields (Stored as JSON Arrays)
    # SQL cannot store a List directly, so we use a JSON column
    # We use sa_column=Column(JSON) to tell the DB to treat this as a JSON string
    description: List[str] = Field(default=[], sa_column=Column(JSON))
    image: List[str] = Field(default=[], sa_column=Column(JSON))
    tags: List[str] = Field(default=[], sa_column=Column(JSON))

    # Relationships
    ratings: List["Rating"] = Relationship(back_populates="place")

    comments: List["Comment"] = Relationship(back_populates="place")


# User <-> Place rating
class Rating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Keys
    # It connects user and place by their id
    user_id: int = Field(foreign_key="user.id")
    place_id: int = Field(foreign_key="place.id")

    # Score tích lũy từ các interactions (1-5 scale)
    # Score này sẽ được dùng để train collaborative filtering model
    score: float = Field(default=0.0)

    # Relationships
    # User can check its relationship by user.ratings.place.....
    user: Optional["User"] = Relationship(back_populates="ratings")            
    place: Optional["Place"] = Relationship(back_populates="ratings")



class PlaceDetailResponse(SQLModel):
    id: int
    name: str
    description: List[str]
    image: List[str]
    tags: List[str]
    province: Optional[str] = None  # Province/location, usually from tags[0]

    
from datetime import datetime

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Keys
    user_id: int = Field(foreign_key="user.id")
    place_id: int = Field(foreign_key="place.id")

    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="comments")
    place: Optional["Place"] = Relationship(back_populates="comments")


class Like(SQLModel, table=True):
    """Table để lưu likes/dislikes của user cho comments và places"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Keys
    user_id: int = Field(foreign_key="user.id")
    
    # Optional foreign keys - hoặc like comment hoặc like place
    comment_id: Optional[int] = Field(default=None, foreign_key="comment.id")
    place_id: Optional[int] = Field(default=None, foreign_key="place.id")
    
    # True=Like, False=Dislike
    # Nếu user bấm lại cùng button -> xóa record này (về trạng thái neutral)
    is_like: Optional[bool] = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# API MODELS (table=False) (not create table in db)
# Used for Requests, Responses, and LLM parsing.
# ==========================================

# --- Recommendation Flow ---

class RecommendRequest(SQLModel):
    user_text: str = Field(..., schema_extra={"example": "i like mountains in Viet Nam"})
    top_k: int = Field(5)

class GroqExtraction(SQLModel):
    location: List[str] = Field(default=[], sa_column=Column(JSON))
    type: str
    budget: str
    weather: str
    crowded: str
    # thêm exclude_locations nếu cần thiết theo prompt cũ của bạn
    exclude_locations: List[str] = []

class PlaceOut(SQLModel):
    id: int
    name: str
    province: str
    themes: List[str]
    score: float
    image: Optional[List[str]] = None

# --- Recommendation Schemas ---

class RecommendationRequest(SQLModel):
    """Schema cho body của request tìm kiếm gợi ý"""
    query: str = Field(..., description="Câu truy vấn mô tả sở thích hoặc địa điểm mong muốn")
    limit: int = Field(default=10, description="Số lượng địa điểm muốn gợi ý")

# Lưu ý: Chúng ta sẽ dùng lại 'PlaceOut' đã có sẵn trong file schemas.py 
# làm model trả về cho Recommendation thay vì tạo PlaceResponse mới.
    
class RecommendResponse(SQLModel):
    extraction: Optional[GroqExtraction] = None
    results: List[PlaceOut]

# --- Rating Flow ---

class InteractionCreate(SQLModel):
    place_id: int
    interaction_type: InteractionType

class RatingCreate(SQLModel):
    place_id: int
    interaction_type: InteractionType = Field(..., description="Type of interaction: like, dislike, click, view, or none")


# --- Auth Flow ---

class UserCreate(SQLModel):
    """Input model - contains raw password"""
    username: str
    password: str 
    # Cho phép user chọn sở thích ngay lúc đăng ký (tùy chọn)
    # preferences: List[str] = []
class UserResponse(SQLModel):
    """Output model - hides password"""
    username: str
    id: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    preferences: List[str] # Trả về preferences để frontend hiển thị
class Token(SQLModel):
    access_token: str
    token_type: str

class UserProfileUpdate(SQLModel):
    """Model for updating user profile"""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None


# Define request body structure for Chatbot
class ChatbotRequest(SQLModel):
    message: str




