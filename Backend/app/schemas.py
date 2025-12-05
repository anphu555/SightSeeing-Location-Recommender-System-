from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, JSON, Column

from enum import Enum

# ==========================================
# DATABASE TABLES (table=True) (create table in db)
# These create the actual rows in your DB.
# ==========================================

# table = true để tạo bảng cho db (trong file sqlite)
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str  # We store the hash, not the raw password

    # Relationships (Optional but recommended)
    ratings: List["Rating"] = Relationship(back_populates="user")

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

# User <-> Place rating
class Rating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Keys
    # It connects user and place by their id
    user_id: int = Field(foreign_key="user.id")
    place_id: int = Field(foreign_key="place.id")

    # Score tích lũy từ các interactions (1-5 scale)
    # Score này sẽ được dùng để train collaborative filtering model
    score: float = Field(default=3.0, ge=1.0, le=5.0)

    # Relationships
    # User can check its relationship by user.ratings.place.....
    user: Optional[User] = Relationship(back_populates="ratings")            
    place: Optional[Place] = Relationship(back_populates="ratings")



class PlaceDetailResponse(SQLModel):
    id: int
    name: str
    description: List[str]
    image: List[str]
    tags: List[str]


# ==========================================
# API MODELS (table=False) (not create table in db)
# Used for Requests, Responses, and LLM parsing.
# ==========================================

# --- Recommendation Flow ---

class RecommendRequest(SQLModel):
    user_text: str = Field(..., schema_extra={"example": "i like mountains in Viet Nam"})
    top_k: int = Field(5, ge=1, le=100)

class GroqExtraction(SQLModel):
    location: List[str] = Field(default=[], sa_column=Column(JSON))
    type: str
    budget: str
    weather: str
    crowded: str
    # thêm exclude_locations nếu cần thiết theo prompt cũ của bạn
    exclude_locations: List[str] = []

class PlaceOut(SQLModel):
    """Used to return place data to the frontend"""
    id: int
    name: str
    country: str
    province: str
    region: str
    themes: List[str]
    score: float # Similarity score (calculated, not from DB)


class PreferenceEnum(str, Enum):
    like = "like"
    dislike = "dislike"
    none = "none"

    
class RecommendResponse(SQLModel):
    extraction: GroqExtraction
    results: List[PlaceOut]

# --- Rating Flow ---

class InteractionType(str, Enum):
    """Các loại tương tác của user với place"""
    like = "like"
    dislike = "dislike"
    click = "click"
    view = "view"  # view > 30s
    none = "none"

class RatingCreate(SQLModel):
    place_id: int
    interaction_type: InteractionType = Field(..., description="Type of interaction: like, dislike, click, view, or none")


# --- Auth Flow ---

class UserCreate(SQLModel):
    """Input model - contains raw password"""
    username: str
    password: str 

class UserResponse(SQLModel):
    """Output model - hides password"""
    username: str
    id: int

class Token(SQLModel):
    access_token: str
    token_type: str


# Define request body structure for Chatbot
class ChatbotRequest(SQLModel):
    message: str