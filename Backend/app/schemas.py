from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from typing import List

class RecommendRequest(BaseModel):
    user_text: str = Field(..., example="i like mountains in Viet Nam and cool weather")
    top_k: int = Field(5, ge=1, le=100)

class GroqExtraction(BaseModel):
    location: List[str]
    type: str
    budget: str
    weather: str
    crowded: str
    # thêm exclude_locations nếu cần thiết theo prompt cũ của bạn
    exclude_locations: List[str] = [] 
class PlaceOut(BaseModel):
    id: int
    name: str
    country: str
    province: str
    region: str
    themes: List[str]
    score: float

class PreferenceEnum(str, Enum):
    like = "like"
    dislike = "dislike"
    none = "none"

# 2. Thêm Schema cho Rating với Enum
class RatingCreate(BaseModel):
    place_id: int
    preference: PreferenceEnum = Field(..., description="Preference for the place: like, dislike, or none")

    
class RecommendResponse(BaseModel):
    extraction: GroqExtraction
    results: List[PlaceOut]

# --- Thêm Schema cho Auth ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str