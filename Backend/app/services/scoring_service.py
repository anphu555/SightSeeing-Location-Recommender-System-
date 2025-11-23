from typing import List, Dict, Any
from app.schemas import GroqExtraction, PlaceOut
from app.data import PLACES # Giả sử bạn đã di chuyển file data.py vào thư mục app

TYPE_TO_THEME = {
    "mountain": ["mountain"],
    "beach": ["beach"],
    "island": ["island", "snorkeling"],
    "forest": ["nature", "forest"],
    "city": ["city", "culture"],
    "unknown": []
}

def score_place(ex: GroqExtraction, place: Dict[str, Any]) -> float:
    prov_boost = 0.0
    if ex.location:
        def norm(s): return s.lower().replace(" ", "")
        user_provs = {norm(p) for p in ex.location}
        if norm(place.get("province", "")) in user_provs:
            prov_boost = 0.6

    target_themes = TYPE_TO_THEME.get(ex.type, [])
    theme_overlap = len(set(t.lower() for t in place["themes"]) & set(t.lower() for t in target_themes))
    theme_score = theme_overlap / max(len(place["themes"]), 1)

    weather_bonus = 0.1 if (ex.weather in {"cool", "cold"} and "cool weather" in [t.lower() for t in place["themes"]]) else 0.0

    return round(prov_boost + theme_score + weather_bonus, 4)

def rank_places(ex: GroqExtraction, top_k: int) -> List[PlaceOut]:
    scored = []
    for p in PLACES:
        s = score_place(ex, p)
        scored.append(PlaceOut(
            name=p["name"],
            country=p["country"],
            province=p["province"],
            region=p["region"],
            themes=p["themes"],
            score=s
        ))
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]