from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app import schemas
from app.database import get_session
from app.routers.auth import get_current_user
from typing import List
from collections import Counter
import numpy as np

# Import functions to access model
from .recsysmodel import get_recsys_model, bert_encode 

router = APIRouter(
    prefix="/recommendation",
    tags=["Recommendation"]
)

# --- UTILS ---
# Sửa PlaceResponse thành schemas.PlaceOut
def get_place_details(place_ids: List[int], db: Session, scores_dict: dict = None) -> List[schemas.PlaceOut]:
    """Lấy chi tiết địa điểm từ DB và trả về theo đúng định dạng PlaceOut."""
    if not place_ids:
        return []
        
    places = db.query(schemas.Place).filter(schemas.Place.id.in_(place_ids)).all()
    
    # Map để giữ đúng thứ tự gợi ý
    place_map = {place.id: place for place in places}
    sorted_places = [place_map.get(pid) for pid in place_ids if pid in place_map]

    # Convert sang PlaceOut - map các trường từ Place model
    results = []
    for place in sorted_places:
        # PlaceOut yêu cầu: id, name, province, themes, score, image
        # Place có: id, name, description, image, tags
        # Map: tags -> themes, tags[0] -> province (nếu có)
        
        # Lấy score thực tế từ scores_dict nếu có, nếu không dùng 0.0
        actual_score = scores_dict.get(place.id, 0.0) if scores_dict else 0.0
        
        place_out = schemas.PlaceOut(
            id=place.id,
            name=place.name,
            province=place.tags[0] if place.tags else "Unknown",  # Lấy tag đầu tiên làm province
            themes=place.tags if place.tags else [],  # tags -> themes
            score=float(actual_score),  # Dùng score thực tế từ model
            image=place.image if place.image else []
        )
        results.append(place_out)
        
    return results

# --- CORE LOGIC ---
def run_two_tower_recommendation(query_text: str, limit: int, db: Session) -> List[schemas.PlaceOut]:
    if not query_text or not query_text.strip():
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Truy vấn không được rỗng.")

    model = get_recsys_model()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation model is not initialized. Please check server logs."
        )

    try:
        model_data = model.model_data
        item_embeddings = model_data['item_embeddings']
        places_df = model_data['places_df']
        user_tower_model = model_data['user_tower_model']
        
        # 1. Encode query
        input_ids_tf, attention_mask_tf = bert_encode([query_text])
        
        # 2. Predict User Vector
        user_vector = user_tower_model.predict(
            [input_ids_tf.numpy(), attention_mask_tf.numpy()], 
            verbose=0
        )
        
        # 3. Dot Product
        scores = np.dot(item_embeddings, user_vector.T).flatten()
        
        # 4. Top N
        top_indices = scores.argsort()[-limit:][::-1]
        
        # 5. Get IDs and Scores
        recommended_place_ids = places_df.iloc[top_indices]['id'].tolist()
        recommended_scores = scores[top_indices].tolist()
        
        # Create score mapping dict
        scores_dict = {place_id: score for place_id, score in zip(recommended_place_ids, recommended_scores)}
        
        # 6. Get Details with scores
        return get_place_details(recommended_place_ids, db, scores_dict)

    except Exception as e:
        print(f"❌ Error Two-Tower Rec: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống gợi ý: {e}"
        )

# --- ENDPOINTS ---

# 1. Popular places - không cần authentication, không cần query
@router.get("/popular-places", response_model=List[schemas.PlaceOut])
def get_popular_places(
    db: Session = Depends(get_session),
    limit: int = 12
):
    """Gợi ý các địa điểm nổi tiếng và phổ biến tại Việt Nam."""
    query_text = "I am looking for a famous and popular tourist destination in Vietnam"
    return run_two_tower_recommendation(query_text, limit, db)

# 2. Dựa trên sở thích User - cần authentication
@router.get("/based-on-user-preference", response_model=List[schemas.PlaceOut])
def get_recommendations_based_on_preference(
    db: Session = Depends(get_session),
    current_user: schemas.User = Depends(get_current_user),
    limit: int = 100
):
    """Gợi ý địa điểm dựa trên lịch sử likes và sở thích của user."""
    
    # 1. Lấy danh sách các places mà user đã like (từ bảng Like)
    liked_places = db.query(schemas.Like).filter(
        schemas.Like.user_id == current_user.id,
        schemas.Like.place_id.isnot(None),  # Chỉ lấy likes cho places (không phải comments)
        schemas.Like.is_like == True  # Chỉ lấy likes, không lấy dislikes
    ).all()
    
    # 2. Lấy thông tin chi tiết các places đã like
    liked_place_ids = [like.place_id for like in liked_places]
    liked_place_objects = db.query(schemas.Place).filter(
        schemas.Place.id.in_(liked_place_ids)
    ).all() if liked_place_ids else []
    
    # 3. Tạo query dựa trên tags của các places đã like
    query_parts = []
    
    # Collect all tags from liked places
    all_tags = []
    for place in liked_place_objects:
        if place.tags:
            all_tags.extend(place.tags)
    
    # Remove province names and common words, keep themes/categories
    theme_keywords = []
    common_provinces = ["Ha Noi", "Da Nang", "Ho Chi Minh", "Hue", "Nha Trang", 
                       "Sapa", "Dalat", "Phu Quoc", "Quang Ninh", "Bac Giang"]
    
    for tag in all_tags:
        # Skip province names
        if tag not in common_provinces:
            theme_keywords.append(tag)
    
    # Get unique themes (most common ones)
    from collections import Counter
    if theme_keywords:
        # Get top 5 most common themes
        theme_counts = Counter(theme_keywords)
        top_themes = [theme for theme, _ in theme_counts.most_common(5)]
        query_parts.append(f"I am interested in {', '.join(top_themes)}")
    
    # 4. Kết hợp với preferences field nếu có
    user_prefs = current_user.preferences
    if user_prefs:
        if isinstance(user_prefs, list):
            query_parts.append(f"I also like {', '.join(user_prefs)}")
        else:
            query_parts.append(f"I also like {user_prefs}")
    
    # 5. Tạo query cuối cùng
    if query_parts:
        query_text = " and ".join(query_parts) + " in Vietnam"
    else:
        # Fallback nếu user chưa có likes và preferences
        query_text = "I am looking for a famous and popular tourist destination in Vietnam"
    
    print(f"🔍 User {current_user.username} recommendation query: {query_text}")
    
    return run_two_tower_recommendation(query_text, limit, db)

# 3. Dựa trên Search Query (Dùng schema mới RecommendationRequest)
@router.post("/search-recommendation", response_model=List[schemas.PlaceOut])
def get_recommendations_based_on_search(
    request: schemas.RecommendationRequest, 
    db: Session = Depends(get_session)
):
    """Tìm kiếm địa điểm dựa trên query text."""
    return run_two_tower_recommendation(request.query, request.limit, db)