from pydantic import BaseModel, Field
from typing import List

class RecommendRequest(BaseModel):
    user_text: str = Field(..., example="i like mountains in Viet Nam and cool weather")
    top_k: int = Field(5, ge=1, le=20)

class GroqExtraction(BaseModel):
    location: List[str]
    type: str
    budget: str
    weather: str
    crowded: str
    # thêm exclude_locations nếu cần thiết theo prompt cũ của bạn
    exclude_locations: List[str] = [] 

class PlaceOut(BaseModel):
    name: str
    country: str
    province: str
    region: str
    themes: List[str]
    score: float

class RecommendResponse(BaseModel):
    extraction: GroqExtraction
    results: List[PlaceOut]