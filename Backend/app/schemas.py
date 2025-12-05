from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, JSON, Column

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

    # Ví dụ: ["Nature", "Beach", "Food"]
    preferences: List[str] = Field(default=[], sa_column=Column(JSON))

    # Relationships (Optional but recommended)
    ratings: List["Rating"] = Relationship(back_populates="user")

    # comments: List["Comment"] = Relationship(back_populates="user")


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

    # comments: List["Comment"] = Relationship(back_populates="place")


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
    user: Optional[User] = Relationship(back_populates="ratings")            
    place: Optional[Place] = Relationship(back_populates="ratings")



# from datetime import datetime

# class Comment(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)

#     # Foreign Keys
#     user_id: int = Field(foreign_key="user.id")
#     place_id: int = Field(foreign_key="place.id")


#     content: str
#     created_at: datetime = Field(default_factory=datetime.utcnow)
    
#     # Relationships
#     user: Optional[User] = Relationship(back_populates="comments")
#     place: Optional[Place] = Relationship(back_populates="comments")



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


# class PreferenceEnum(str, Enum):
#     like = "like"
#     dislike = "dislike"
#     none = "none"

    
class RecommendResponse(SQLModel):
    extraction: GroqExtraction
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
    preferences: List[str] # Trả về preferences để frontend hiển thị
class Token(SQLModel):
    access_token: str
    token_type: str


# Define request body structure for Chatbot
class ChatbotRequest(SQLModel):
    message: str




