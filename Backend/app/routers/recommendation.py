from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import database, models, schemas
from app.security import get_current_user
from typing import List
import numpy as np

# Import model
from .recsysmodel import RECSYS_MODEL, bert_encode 

router = APIRouter(
    prefix="/recommendation",
    tags=["Recommendation"]
)

# --- UTILS ---
# Sửa PlaceResponse thành schemas.PlaceOut
def get_place_details(place_ids: List[int], db: Session) -> List[schemas.PlaceOut]:
    """Lấy chi tiết địa điểm từ DB và trả về theo đúng định dạng PlaceOut."""
    if not place_ids:
        return []
        
    places = db.query(models.Place).filter(models.Place.id.in_(place_ids)).all()
    
    # Map để giữ đúng thứ tự gợi ý
    place_map = {place.id: place for place in places}
    sorted_places = [place_map.get(pid) for pid in place_ids if pid in place_map]

    # Convert sang PlaceOut (SQLModel tự động validate từ ORM object)
    # Lưu ý: PlaceOut cần các trường province_name, tags... bạn cần đảm bảo query lấy đủ hoặc model Place có relationship
    results = []
    for place in sorted_places:
        # Logic đơn giản để map từ DB model sang Schema nếu cần xử lý thêm
        # Nếu cấu trúc Place và PlaceOut khớp nhau, có thể dùng .from_orm hoặc validate trực tiếp
        results.append(schemas.PlaceOut.model_validate(place))
        
    return results

# --- CORE LOGIC ---
def run_two_tower_recommendation(query_text: str, limit: int, db: Session) -> List[schemas.PlaceOut]:
    if not query_text or not query_text.strip():
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Truy vấn không được rỗng.")

    try:
        model_data = RECSYS_MODEL.model_data
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
        
        # 5. Get IDs
        recommended_place_ids = places_df.iloc[top_indices]['id'].tolist()
        
        # 6. Get Details
        return get_place_details(recommended_place_ids, db)

    except Exception as e:
        print(f"❌ Error Two-Tower Rec: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống gợi ý: {e}"
        )

# --- ENDPOINTS ---

# 1. Dựa trên sở thích User
@router.get("/based-on-user-preference", response_model=List[schemas.PlaceOut])
def get_recommendations_based_on_preference(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 10
):
    user_prefs = current_user.preferences
    
    # Fallback query tiếng Anh để model hiểu tốt nhất (như đã bàn ở trên)
    if not user_prefs:
        query_text = "I am looking for a famous and popular tourist destination in Vietnam"
    else:
        # Nếu preferences là list JSON, join lại thành string
        if isinstance(user_prefs, list):
             query_text = f"I am interested in {' '.join(user_prefs)}"
        else:
             query_text = f"I am interested in {user_prefs}"
            
    return run_two_tower_recommendation(query_text, limit, db)

# 2. Dựa trên Search Query (Dùng schema mới RecommendationRequest)
@router.post("/search-recommendation", response_model=List[schemas.PlaceOut])
def get_recommendations_based_on_search(
    request: schemas.RecommendationRequest, 
    db: Session = Depends(database.get_db)
):
    return run_two_tower_recommendation(request.query, request.limit, db)