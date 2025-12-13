# ==========================================
# CONTENT-BASED RECOMMENDATION SYSTEM
# Thay thế Two-Tower Model bằng Content-Based Filtering
# ==========================================

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlmodel import Session, select
from typing import Optional
import unicodedata

from app.schemas import Place, Rating, Like

# ==========================================
# HELPER FUNCTION: Remove Vietnamese Diacritics
# ==========================================

def remove_diacritics(text: str) -> str:
    """
    Remove Vietnamese diacritics from text for matching purposes.
    Example: "Quảng Ninh" -> "Quang Ninh"
    """
    if not text:
        return text
    # Normalize to NFD (decompose characters)
    nfd = unicodedata.normalize('NFD', text)
    # Filter out combining characters (diacritics)
    without_diacritics = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return without_diacritics

# ==========================================
# 1. LOAD DỮ LIỆU TỪ DATABASE.DB
# ==========================================

def load_places_from_db():
    """Load tất cả places từ database.db vào DataFrame"""
    # Import get_session thay vì dùng engine trực tiếp
    from app.database import get_session
    
    # Sử dụng context manager đúng cách với generator
    session_gen = get_session()
    session = next(session_gen)
    
    try:
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
    finally:
        # Đảm bảo đóng session
        try:
            next(session_gen)
        except StopIteration:
            pass

# LAZY LOADING: Chỉ load khi cần, không load ngay khi import module
items_df = None
count_matrix = None
vectorizer = None

def initialize_recsys():
    """Khởi tạo RecSys model - gọi hàm này sau khi database đã được tạo"""
    global items_df, count_matrix, vectorizer
    
    if items_df is not None:
        return  # Đã khởi tạo rồi
    
    try:
        # Load data từ database
        items_df = load_places_from_db()
        
        if len(items_df) == 0:
            print("Warning: No places found in database")
            return
        
        # Khởi tạo vectorizer
        vectorizer = CountVectorizer(stop_words='english', max_features=5000)
        count_matrix = vectorizer.fit_transform(items_df['soup'])
        
        print(f"RecSys initialized with {len(items_df)} places")
    except Exception as e:
        print(f"Failed to initialize RecSys: {e}")
        items_df = pd.DataFrame()  # Empty dataframe để tránh lỗi

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

def get_user_likes(user_id: int):
    """
    Lấy danh sách place_id mà user đã like
    Returns: List[int] - Danh sách place_id
    """
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        statement = select(Like).where(
            Like.user_id == user_id,
            Like.place_id.isnot(None)  # Chỉ lấy likes cho place, không lấy likes cho comment
        )
        likes = session.exec(statement).all()
        return [like.place_id for like in likes]
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

def build_user_profile(user_id: int):
    """
    Tạo vector sở thích người dùng dựa trên:
    1. Rating history: Score cao (4-5) → Positive, Score thấp (1-2) → Negative
    2. Like interactions: Like → Strong positive signal (tương đương rating 4.5)
    
    Chiến lược:
    - Rating có weight dựa trên score (1-5)
    - Like được tính như một positive signal mạnh (weight = 0.75)
    - Kết hợp cả hai để tạo user profile toàn diện
    """
    from app.database import get_session
    
    # Lấy ratings từ database
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        statement = select(Rating).where(Rating.user_id == user_id)
        ratings = session.exec(statement).all()
        
        # Lấy likes từ database
        liked_place_ids = get_user_likes(user_id)
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass
    
    # Nếu không có tương tác nào → Cold start
    if not ratings and not liked_place_ids:
        return None

    # Khởi tạo vector rỗng
    if count_matrix is None:
        return None
        
    user_profile = np.zeros(count_matrix.shape[1])
    interaction_count = 0
    
    # 1. XỬ LÝ RATINGS
    for rating in ratings:
        item_vec = get_item_vector(rating.place_id)
        if item_vec is not None:
            # Chuyển đổi score (1-5) thành weight (-1 đến +1)
            # Score 5 → +1, Score 3 → 0, Score 1 → -1
            weight = (rating.score - 3.0) / 2.0  # Normalize về [-1, 1]
            
            user_profile += weight * item_vec.toarray()[0]
            interaction_count += 1
    
    # 2. XỬ LÝ LIKES
    # Like = strong positive signal (tương đương rating 4.5 → weight = 0.75)
    LIKE_WEIGHT = 0.75
    
    for place_id in liked_place_ids:
        item_vec = get_item_vector(place_id)
        if item_vec is not None:
            user_profile += LIKE_WEIGHT * item_vec.toarray()[0]
            interaction_count += 1
            
    if interaction_count == 0:
        return None
        
    return user_profile

# 4. HÀM RECOMMEND CHÍNH (Content-Based với User History)
def recommend_content_based(user_prefs_tags, user_id: Optional[int] = None, top_k: int = 10):
    """
    Hàm gợi ý dựa trên Content-Based Filtering + User History
    
    Args:
        user_prefs_tags (list): List các tags user quan tâm (từ prompt hoặc preferences)
        user_id (int, optional): ID người dùng để lấy lịch sử ratings
        top_k (int): Số lượng gợi ý trả về
    
    Returns:
        pd.DataFrame: DataFrame chứa các địa điểm được gợi ý với score
    """
    # Đảm bảo RecSys đã được khởi tạo
    initialize_recsys()
    
    if count_matrix is None or items_df is None or len(items_df) == 0:
        return pd.DataFrame()  # Return empty dataframe
    
    # --- BƯỚC 1: XÂY DỰNG QUERY VECTOR TỪ TAGS ---
    search_query = " ".join(user_prefs_tags) if user_prefs_tags else ""
    
    # Tạo vector từ tags
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
        # Không có prompt, không có history → Trả về DIVERSE/POPULAR items
        results = items_df.copy()
        
        # Tạo diversity score: kết hợp random và position để tạo sự đa dạng
        # Thay vì trả về theo thứ tự ID, shuffle để mỗi lần khác nhau
        results = results.sample(frac=1, random_state=None).reset_index(drop=True)
        results['score'] = 0.5  # Neutral score cho tất cả
        
        # Thêm province từ tags (tag đầu tiên)
        results['province'] = results['tags'].apply(lambda x: x[0] if x and len(x) > 0 else 'Vietnam')
        return results.head(top_k)

    # Tính Cosine Similarity
    cosine_sim = cosine_similarity([final_vec], count_matrix)
    scores = cosine_sim[0]
    
    # Tạo bảng kết quả
    results = items_df.copy()
    results['score'] = scores
    
    # Thêm cột province (lấy từ tag đầu tiên)
    results['province'] = results['tags'].apply(lambda x: x[0] if x and len(x) > 0 else 'Vietnam')
    
    # --- BƯỚC 4: LỌC THEO LOCATION (NẾU CÓ) ---
        # Danh sách các từ khóa tỉnh/thành phố Việt Nam (bao gồm cả có và không dấu)
    province_keywords = [
        'hanoi', 'hà nội', 'ha noi',
        'saigon', 'ho chi minh', 'hồ chí minh', 'hcm',
        'danang', 'đà nẵng', 'da nang',
        'hue', 'huế',
        'nhatrang', 'nha trang',
        'dalat', 'đà lạt', 'da lat',
        'hoi an', 'hội an',
        'phu quoc', 'phú quốc', 'phu quốc',
        'sapa', 'sa pa',
        'quang ninh', 'quảng ninh',
        'halong', 'hạ long', 'ha long',
        'vung tau', 'vũng tàu',
        'quy nhon', 'quy nhơn',
        'can tho', 'cần thơ',
        'ninh binh', 'ninh bình',
        'quang binh', 'quảng bình',
        'binh thuan', 'bình thuận',
        'lam dong', 'lâm đồng',
        'kien giang', 'kiên giang',
        'ba ria', 'bà rịa',
        'thanh hoa', 'thanh hóa',
        'nghe an', 'nghệ an',
        'hai phong', 'hải phòng'
    ]
    
    # Tìm location tags từ user_prefs_tags
    location_tags = [tag for tag in user_prefs_tags if any(province_keyword in remove_diacritics(tag.lower()) for province_keyword in province_keywords)]
    
    if location_tags:
        # Normalize và lowercase location tags để so sánh
        location_tags_normalized = [remove_diacritics(loc.lower().strip()) for loc in location_tags]
        
        def matches_location(tags_list):
            if not tags_list:
                return False
            # Normalize tags trong database để so sánh
            tags_normalized = [remove_diacritics(tag.lower()) for tag in tags_list]
            return any(
                any(user_loc in tag for user_loc in location_tags_normalized)
                for tag in tags_normalized
            )
        
        # Filter places có tags chứa location
        mask = results['tags'].apply(matches_location)
        filtered = results[mask]
        
        # Nếu filter quá chặt (không còn kết quả), giữ nguyên
        if len(filtered) > 0:
            results = filtered

    # Sắp xếp giảm dần theo score và lấy top_k
    results = results.sort_values(by='score', ascending=False).head(top_k)
    
    # Đảm bảo các cột cần thiết tồn tại
    results = results[['id', 'name', 'tags', 'province', 'score']].copy()
    
    return results

# Wrapper function để tương thích với recommendation.py (thay thế two-tower)
def recommend_two_tower(user_prefs_tags, user_id=None, top_k=10):
    """
    Wrapper function tương thích với interface của two-tower model.
    Sử dụng Content-Based Filtering thay vì Two-Tower.
    
    Args:
        user_prefs_tags (list): List các tags user thích
        user_id (int, optional): ID người dùng để lấy lịch sử tương tác
        top_k (int): Số lượng gợi ý trả về
    
    Returns:
        pd.DataFrame: DataFrame chứa các địa điểm được gợi ý
    """
    return recommend_content_based(user_prefs_tags, user_id=user_id, top_k=top_k)

# Hàm recommend cũ (giữ lại để backward compatibility)
def recommend(user_prompt_extraction, user_id: Optional[int] = None):
    """
    Hàm cũ - giữ lại để tương thích với code cũ
    user_prompt_extraction: Kết quả JSON từ LLM (user_text)
    user_id: ID người dùng để lấy lịch sử ratings
    """
    # Chuyển đổi extraction thành tags list
    search_keywords = []
    
    if hasattr(user_prompt_extraction, 'type') and user_prompt_extraction.type and user_prompt_extraction.type != 'unknown':
        search_keywords.append(user_prompt_extraction.type)
        
    if hasattr(user_prompt_extraction, 'location'):
        for loc in user_prompt_extraction.location:
            search_keywords.append(loc)
        
    if hasattr(user_prompt_extraction, 'weather') and user_prompt_extraction.weather and user_prompt_extraction.weather != 'unknown':
        search_keywords.append(user_prompt_extraction.weather)
    
    # Gọi hàm mới
    return recommend_content_based(search_keywords, user_id=user_id, top_k=10)