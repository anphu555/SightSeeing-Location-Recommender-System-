from typing import List, Dict, Any
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