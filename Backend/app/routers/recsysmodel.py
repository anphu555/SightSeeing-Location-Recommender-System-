import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlmodel import Session, select
from typing import Optional

from app.schemas import Place, Rating
from app.database import engine

# ==========================================
# 1. LOAD DỮ LIỆU TỪ DATABASE.DB
# ==========================================

def load_places_from_db():
    """Load tất cả places từ database.db vào DataFrame"""
    with Session(engine) as session:
        statement = select(Place)
        places = session.exec(statement).all()
        
        # Chuyển đổi sang list of dict
        places_data = []
        for place in places:
            # Kết hợp các fields thành text để vectorize
            # tags là List[str], description cũng là List[str]
            tags_text = " ".join(place.tags) if place.tags else ""
            desc_text = " ".join(place.description) if place.description else ""
            
            places_data.append({
                "id": place.id,
                "name": place.name,
                "tags": place.tags,
                "description": place.description,
                "images": place.image,
                # Tạo soup để vectorize
                "soup": f"{place.name} {tags_text} {desc_text}"
            })
        
        return pd.DataFrame(places_data)

# Load data khi module được import
items_df = load_places_from_db()

# 2. TẠO FEATURE SOUP (ĐÃ TẠO TRONG load_places_from_db)
# items_df đã có cột 'soup' rồi

# 3. KHỞI TẠO MODEL (CountVectorizer)
vectorizer = CountVectorizer(stop_words='english', max_features=5000)
try:
    if len(items_df) > 0:
        count_matrix = vectorizer.fit_transform(items_df['soup'])
    else:
        count_matrix = None
except ValueError:
    print("Not enough data to fit vectorizer")
    count_matrix = None

# --- HÀM HỖ TRỢ ---

def get_item_vector(item_id):
    """Lấy vector của một địa điểm dựa trên ID"""
    if count_matrix is None:
        return None
    try:
        idx = items_df.index[items_df['id'] == item_id].tolist()[0]
        return count_matrix[idx]
    except (IndexError, KeyError):
        return None

def build_user_profile(user_id: int):
    """
    Tạo vector sở thích người dùng dựa trên Rating history
    Score cao (4-5) → Positive influence
    Score thấp (1-2) → Negative influence
    """
    with Session(engine) as session:
        statement = select(Rating).where(Rating.user_id == user_id)
        ratings = session.exec(statement).all()
        
        if not ratings:
            return None  # User mới hoàn toàn (Cold start)

    # Khởi tạo vector rỗng
    if count_matrix is None:
        return None
        
    user_profile = np.zeros(count_matrix.shape[1])
    interaction_count = 0
    
    for rating in ratings:
        item_vec = get_item_vector(rating.place_id)
        if item_vec is not None:
            # Chuyển đổi score (1-5) thành weight (-1 đến +1)
            # Score 5 → +1, Score 3 → 0, Score 1 → -1
            weight = (rating.score - 3.0) / 2.0  # Normalize về [-1, 1]
            
            user_profile += weight * item_vec.toarray()[0]
            interaction_count += 1
            
    if interaction_count == 0:
        return None
        
    return user_profile

# 4. HÀM RECOMMEND CHÍNH
def recommend(user_prompt_extraction, user_id: Optional[int] = None):
    """
    user_prompt_extraction: Kết quả JSON từ LLM (user_text)
    user_id: ID người dùng để lấy lịch sử ratings
    """
    
    if count_matrix is None or len(items_df) == 0:
        return items_df  # Return empty or fallback
    
    # --- BƯỚC 1: XÂY DỰNG QUERY VECTOR TỪ PROMPT ---
    search_keywords = []
    
    # Lấy thông tin từ extraction
    if user_prompt_extraction.type and user_prompt_extraction.type != 'unknown':
        search_keywords.append(user_prompt_extraction.type)
        
    for loc in user_prompt_extraction.location:
        search_keywords.append(loc)
        
    if user_prompt_extraction.weather and user_prompt_extraction.weather != 'unknown':
        search_keywords.append(user_prompt_extraction.weather)

    search_query = " ".join(search_keywords)
    
    # Tạo vector từ prompt
    try:
        query_vec = vectorizer.transform([search_query]).toarray()[0]
    except:
        query_vec = np.zeros(count_matrix.shape[1])

    # --- BƯỚC 2: KẾT HỢP VỚI LỊCH SỬ USER (NẾU CÓ) ---
    if user_id:
        user_profile_vec = build_user_profile(user_id)
        if user_profile_vec is not None:
            # HYBRID: 70% Prompt + 30% User History
            final_vec = (query_vec * 0.7) + (user_profile_vec * 0.3)
        else:
            final_vec = query_vec
    else:
        final_vec = query_vec

    # --- BƯỚC 3: TÍNH TOÁN ---
    if np.all(final_vec == 0):
        # Không có prompt, không có history → Trả về top items
        results = items_df.copy()
        results['score'] = 0.5  # Default score
        return results.head(10)

    # Tính Cosine Similarity
    cosine_sim = cosine_similarity([final_vec], count_matrix)
    scores = cosine_sim[0]
    
    # Tạo bảng kết quả
    results = items_df.copy()
    results['score'] = scores
    
    # --- BƯỚC 4: LỌC THEO LOCATION (NẾU CÓ) ---
    # Note: Schema mới không có trường 'province', chỉ có 'tags'
    # Bạn có thể lọc theo tags nếu tags chứa tên địa danh
    if user_prompt_extraction.location:
        user_locations_lower = [loc.lower().strip() for loc in user_prompt_extraction.location]
        
        def matches_location(tags_list):
            if not tags_list:
                return False
            tags_lower = [tag.lower() for tag in tags_list]
            return any(
                any(user_loc in tag for user_loc in user_locations_lower)
                for tag in tags_lower
            )
        
        # Filter places có tags chứa location
        mask = results['tags'].apply(matches_location)
        filtered = results[mask]
        
        # Nếu filter quá chặt (không còn kết quả), giữ nguyên
        if len(filtered) > 0:
            results = filtered

    # Sắp xếp giảm dần theo score
    results = results.sort_values(by='score', ascending=False)
    
    return results