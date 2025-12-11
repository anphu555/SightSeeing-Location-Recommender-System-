from typing import List, Dict, Any
# from backend.app.old.schemas import GroqExtraction, PlaceOut
from app.schemas import GroqExtraction, PlaceOut
from app.services.db_service import get_all_places 

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
                id=p["id"],  # <--- QUAN TRỌNG: Thêm dòng này để sửa lỗi
                name=p["name"],
                country=p.get("country", "Vietnam"),
                province=p.get("province") or "",
                region=p.get("region") or "",
                themes=p.get("themes", []),
                score=s
            ))
            
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]

def calculate_interest_score(interactions: Dict[str, Any]) -> int:
    """
    DEPRECATED: Use calculate_user_place_score() instead.
    Kept for backward compatibility.
    """
    score = 5  # Start with a neutral score

    if interactions.get("disliked"):
        return 1

    if interactions.get("liked"):
        return 10

    if interactions.get("clicked"):
        score = 6  # Initial interest shown by clicking
        time_spent = interactions.get("time_spent_seconds", 0)

        if time_spent < 10:
            score -= 2  # Quick bounce, not interested
        elif time_spent <= 30:
            pass  # Neutral interest
        elif time_spent <= 60:
            score += 1  # Shows interest
        else:
            score += 2  # Shows strong interest
    
    # Ensure score is within 1-10 range
    return max(1, min(10, score))


def calculate_user_place_score(
    search_similarity: int = 0,
    like: bool = False,
    dislike: bool = False,
    watch_time_seconds: int = 0
) -> float:
    """
    Calculate cumulative score for a user-place interaction based on multiple signals.
    
    Scoring Rules:
    - Each search with similar themes: +0.5 points
    - Dislike: set final score to 1 (negative signal)
    - Like: set final score to 10 (strong positive signal)
    - Watch time:
        * Quick bounce (<10s): -2 points
        * Moderate time (10-60s): +1 point
        * Extended time (>60s): +2 points
    
    Args:
        search_similarity (int): Number of times this place appeared in searches with similar themes
        like (bool): True if user liked this place
        dislike (bool): True if user disliked this place
        watch_time_seconds (int): Total time spent viewing this place
        
    Returns:
        float: Calculated score, clamped between 0.0 and 10.0
    """
    # Priority 1: Explicit feedback overrides everything
    if like:
        return 10.0
    
    if dislike:
        return 1.0
    
    # Priority 2: Calculate cumulative score from implicit signals
    score = 0.0
    
    # Search similarity bonus: 0.5 per similar search
    score += search_similarity * 0.5
    
    # Watch time signals
    if watch_time_seconds > 0:
        if watch_time_seconds < 10:
            # Quick bounce - negative signal
            score += -2.0
        elif watch_time_seconds <= 60:
            # Moderate engagement
            score += 1.0
        else:
            # Strong engagement
            score += 2.0
    
    # Clamp score between 0 and 10
    return max(0.0, min(10.0, score))


def update_score_on_search_similarity(current_score: float) -> float:
    """
    Update score when a place appears in search results with similar themes.
    Each appearance adds 0.5 points.
    
    Args:
        current_score (float): Current rating score
        
    Returns:
        float: Updated score, clamped to max 10.0
    """
    new_score = current_score + 0.5
    return min(10.0, new_score)


def update_score_on_like(current_score: float) -> float:
    """
    Update score when user likes a place.
    Like sets score to 10 (maximum).
    
    Args:
        current_score (float): Current rating score (ignored)
        
    Returns:
        float: 10.0 (maximum score)
    """
    return 10.0


def update_score_on_dislike(current_score: float) -> float:
    """
    Update score when user dislikes a place.
    Dislike sets score to 1 (minimum positive).
    
    Args:
        current_score (float): Current rating score (ignored)
        
    Returns:
        float: 1.0 (minimum score)
    """
    return 1.0


def update_score_on_watch_time(current_score: float, watch_time_seconds: int) -> float:
    """
    Update score based on how long user viewed the place.
    
    Rules:
    - Quick bounce (<10s): -2 points
    - Moderate time (10-60s): +1 point
    - Extended time (>60s): +2 points
    
    Args:
        current_score (float): Current rating score
        watch_time_seconds (int): Time spent viewing in seconds
        
    Returns:
        float: Updated score, clamped between 0.0 and 10.0
    """
    if watch_time_seconds < 10:
        delta = -2.0
    elif watch_time_seconds <= 60:
        delta = 1.0
    else:
        delta = 2.0
    
    new_score = current_score + delta
    return max(0.0, min(10.0, new_score))