"""
Service for calculating user-place rating scores based on various interactions.

Rating scale: 1-5 (with decimals allowed)

Rules:
1. Like: +4 to current score
2. Dislike: score = 1 (lowest) OR -5 from current score
3. Comment: +0.5 (only counted once)
4. View time (in seconds):
   - < 5 seconds: accidental click, no change
   - 5-90 seconds: proportional score (2.5 to 4)
   - > 90 seconds: 4 points max
   - On subsequent views: update only if new score is higher
"""

from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from app.schemas import GroqExtraction, PlaceOut, Rating, Comment
from app.services.db_service import get_all_places 

# ==========================================
# RECOMMENDATION SCORING (Original Functions)
# ==========================================

TYPE_TO_THEME = {
    "mountain": ["mountain", "peak", "hill", "hiking"],
    "beach": ["beach", "sea", "island", "coast"],
    "island": ["island", "snorkeling", "bay"],
    "forest": ["nature", "forest", "park", "national park"],
    "city": ["city", "culture", "museum", "hotel", "building"],
    "unknown": []
}

def score_place(ex: GroqExtraction, place: Dict[str, Any]) -> float:
    prov_boost = 0.0
    if ex.location:
        def norm(s): return s.lower().replace(" ", "") if s else ""
        
        # Lấy province từ DB, đảm bảo không None
        place_prov = place.get("province", "") or ""
        
        user_provs = {norm(p) for p in ex.location}
        if norm(place_prov) in user_provs:
            prov_boost = 0.6

    # Logic tính điểm dựa trên themes (đã được convert từ kind trong db_service)
    target_themes = TYPE_TO_THEME.get(ex.type, [])
    place_themes = place.get("themes", [])
    
    theme_overlap = len(set(t.lower() for t in place_themes) & set(t.lower() for t in target_themes))
    theme_score = theme_overlap / max(len(place_themes), 1)

    # Logic thời tiết (giữ nguyên)
    weather_bonus = 0.1 if (ex.weather in {"cool", "cold"} and "cool weather" in [t.lower() for t in place_themes]) else 0.0

    return round(prov_boost + theme_score + weather_bonus, 4)

def rank_places(ex: GroqExtraction, top_k: int) -> List[PlaceOut]:
    db_places = get_all_places() 
    
    scored = []
    for p in db_places:
        s = score_place(ex, p)
        
        if s > 0: 
            scored.append(PlaceOut(
                id=p["id"],
                name=p["name"],
                province=p.get("province") or "",
                themes=p.get("themes", []),
                score=s
            ))
            
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]


# ==========================================
# USER-PLACE RATING SCORING (New Algorithm)
# ==========================================

class RatingScorer:
    """Service for calculating user-place rating scores (1-5 scale)"""
    
    # Constants
    MIN_VIEW_TIME = 5  # seconds - below this is considered accidental click
    MAX_VIEW_TIME = 90  # seconds - 1.5 minutes
    MIN_VIEW_SCORE = 2.5  # score for minimum valid view time (5 seconds)
    MAX_VIEW_SCORE = 4.0  # maximum score from view time
    
    LIKE_BONUS = 4.0
    DISLIKE_PENALTY = -5.0
    DISLIKE_MIN_SCORE = 1.0
    COMMENT_BONUS = 0.5
    
    MIN_SCORE = 1.0
    MAX_SCORE = 5.0
    
    @staticmethod
    def calculate_view_time_score(view_time_seconds: float) -> Optional[float]:
        """
        Calculate score based on view time.
        
        Args:
            view_time_seconds: Time spent viewing in seconds
            
        Returns:
            Score between 1.5 and 4.0, or None if view time is too short
        """
        # Ignore accidental clicks
        if view_time_seconds < RatingScorer.MIN_VIEW_TIME:
            return None
        
        # Cap at max view time
        capped_time = min(view_time_seconds, RatingScorer.MAX_VIEW_TIME)
        
        # Linear interpolation from min view score (2.5) to max view score (4.0)
        # Formula: score = 2.5 + (time - 5) / (90 - 5) * (4.0 - 2.5)
        time_range = RatingScorer.MAX_VIEW_TIME - RatingScorer.MIN_VIEW_TIME
        score_range = RatingScorer.MAX_VIEW_SCORE - RatingScorer.MIN_VIEW_SCORE
        
        score = RatingScorer.MIN_VIEW_SCORE + (
            (capped_time - RatingScorer.MIN_VIEW_TIME) / time_range * score_range
        )
        
        return round(score, 2)
    
    @staticmethod
    def calculate_rating_score(
        user_id: int,
        place_id: int,
        session: Session,
        view_time_seconds: Optional[float] = None,
        is_like: Optional[bool] = None,
        has_commented: Optional[bool] = None
    ) -> float:
        """
        Calculate the rating score for a user-place pair based on all interactions.
        
        Args:
            user_id: User ID
            place_id: Place ID
            session: Database session
            view_time_seconds: Time spent viewing (optional)
            is_like: True for like, False for dislike, None for no change
            has_commented: Whether user has commented (optional)
            
        Returns:
            Calculated score between 1.0 and 5.0
        """
        # Get existing rating if any
        statement = select(Rating).where(
            Rating.user_id == user_id,
            Rating.place_id == place_id
        )
        existing_rating = session.exec(statement).first()
        
        # Start with existing score or 0
        current_score = existing_rating.score if existing_rating else 0.0
        has_existing_rating = existing_rating is not None
        
        # 1. Handle view time
        # If no existing rating: use view time score
        # If existing rating: only update if new view score is higher
        if view_time_seconds is not None:
            view_score = RatingScorer.calculate_view_time_score(view_time_seconds)
            if view_score is not None:
                if not has_existing_rating:
                    current_score = view_score
                elif view_score > current_score:
                    current_score = view_score
        
        # 2. Handle like/dislike
        if is_like is not None:
            if is_like:
                # Like: +4 to current score
                current_score += RatingScorer.LIKE_BONUS
            else:
                # Dislike: -5 from current score or set to minimum
                current_score += RatingScorer.DISLIKE_PENALTY
                # Ensure it doesn't go below minimum
                current_score = max(current_score, RatingScorer.DISLIKE_MIN_SCORE)
        
        # 3. Handle comment (only add once)
        if has_commented:
            # Check if user has already commented
            comment_statement = select(Comment).where(
                Comment.user_id == user_id,
                Comment.place_id == place_id
            )
            comment_count = len(session.exec(comment_statement).all())
            
            # Only add bonus for the first comment
            if comment_count == 1:
                current_score += RatingScorer.COMMENT_BONUS
        
        # 4. Clamp score to valid range [1.0, 5.0]
        final_score = max(RatingScorer.MIN_SCORE, min(current_score, RatingScorer.MAX_SCORE))
        
        return round(final_score, 2)
    
    @staticmethod
    def update_rating(
        user_id: int,
        place_id: int,
        session: Session,
        view_time_seconds: Optional[float] = None,
        is_like: Optional[bool] = None,
        has_commented: Optional[bool] = None
    ) -> Rating:
        """
        Update or create rating based on user interactions.
        
        Args:
            user_id: User ID
            place_id: Place ID
            session: Database session
            view_time_seconds: Time spent viewing (optional)
            is_like: True for like, False for dislike, None for no change
            has_commented: Whether user has commented (optional)
            
        Returns:
            Updated or created Rating object
        """
        # Calculate new score
        new_score = RatingScorer.calculate_rating_score(
            user_id=user_id,
            place_id=place_id,
            session=session,
            view_time_seconds=view_time_seconds,
            is_like=is_like,
            has_commented=has_commented
        )
        
        # Get or create rating
        statement = select(Rating).where(
            Rating.user_id == user_id,
            Rating.place_id == place_id
        )
        rating = session.exec(statement).first()
        
        if rating:
            rating.score = new_score
        else:
            rating = Rating(
                user_id=user_id,
                place_id=place_id,
                score=new_score
            )
            session.add(rating)
        
        session.commit()
        session.refresh(rating)
        
        return rating