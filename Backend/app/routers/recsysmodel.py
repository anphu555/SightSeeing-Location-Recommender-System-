# ==========================================
# CONTENT-BASED RECOMMENDATION SYSTEM
# Thay thế Two-Tower Model bằng Content-Based Filtering
# ==========================================

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlmodel import Session, select
from typing import Optional
from collections import Counter

from app.schemas import Place, Rating, Like

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
item_similarity_matrix = None  # Item-Item similarity for collaborative filtering
place_popularity = None  # Popularity scores

def initialize_recsys():
    """Khởi tạo RecSys model - gọi hàm này sau khi database đã được tạo"""
    global items_df, count_matrix, vectorizer, item_similarity_matrix, place_popularity
    
    if items_df is not None:
        return  # Đã khởi tạo rồi
    
    try:
        # Load data từ database
        items_df = load_places_from_db()
        
        if len(items_df) == 0:
            print("Warning: No places found in database")
            return
        
        # Khởi tạo TF-IDF vectorizer (thay vì Count)
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),  # Unigrams + bigrams
            min_df=1,  # Xuất hiện ít nhất 1 lần
            max_df=0.8  # Không quá phổ biến (>80%)
        )
        count_matrix = vectorizer.fit_transform(items_df['soup'])
        
        # Tính item-item similarity matrix cho collaborative filtering
        item_similarity_matrix = cosine_similarity(count_matrix, count_matrix)
        
        # Tính popularity scores từ database
        place_popularity = calculate_popularity_scores()
        
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

def calculate_popularity_scores():
    """Tính popularity score cho từng place dựa trên ratings và likes"""
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        all_ratings = session.exec(select(Rating)).all()
        all_likes = session.exec(select(Like).where(Like.place_id.isnot(None))).all()
        
        popularity = Counter()
        
        # Count từ ratings (weighted by score)
        for rating in all_ratings:
            popularity[rating.place_id] += rating.score / 5.0  # Normalize to 0-1
        
        # Count từ likes (strong signal)
        for like in all_likes:
            if like.is_like:
                popularity[like.place_id] += 1.5  # Like = strong positive
            else:
                popularity[like.place_id] -= 0.5  # Dislike = negative
        
        # Normalize to 0-1 range
        if popularity:
            max_pop = max(popularity.values())
            if max_pop > 0:
                popularity = {pid: score/max_pop for pid, score in popularity.items()}
        
        return popularity
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

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
            Like.place_id.isnot(None),
            Like.is_like == True
        )
        likes = session.exec(statement).all()
        return [like.place_id for like in likes]
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

def get_user_dislikes(user_id: int):
    """Lấy danh sách place_id mà user đã dislike"""
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        statement = select(Like).where(
            Like.user_id == user_id,
            Like.place_id.isnot(None),
            Like.is_like == False
        )
        dislikes = session.exec(statement).all()
        return [dislike.place_id for dislike in dislikes]
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

def build_user_profile(user_id: int):
    """
    Tạo vector sở thích người dùng dựa trên:
    1. Rating history: Score cao (4-5) → Positive, Score thấp (1-2) → Negative
    2. Like interactions: Like → Strong positive signal
    3. Dislike interactions: Dislike → Strong negative signal
    
    Chiến lược:
    - Rating có weight dựa trên score (1-5), với emphasis trên high ratings
    - Like được tính như một positive signal rất mạnh (weight = 1.2)
    - Dislike được tính như negative signal (weight = -1.0)
    - Kết hợp cả ba để tạo user profile toàn diện
    """
    from app.database import get_session
    
    # Lấy ratings từ database
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        statement = select(Rating).where(Rating.user_id == user_id)
        ratings = session.exec(statement).all()
        
        # Lấy likes và dislikes từ database
        liked_place_ids = get_user_likes(user_id)
        disliked_place_ids = get_user_dislikes(user_id)
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass
    
    # Nếu không có tương tác nào → Cold start
    if not ratings and not liked_place_ids and not disliked_place_ids:
        return None, set(), set()

    # Khởi tạo vector rỗng
    if count_matrix is None:
        return None, set(), set()
        
    user_profile = np.zeros(count_matrix.shape[1])
    total_weight = 0.0
    
    # Track places đã interact để filter sau
    interacted_places = set()
    
    # 1. XỬ LÝ RATINGS với exponential weighting
    for rating in ratings:
        item_vec = get_item_vector(rating.place_id)
        if item_vec is not None:
            interacted_places.add(rating.place_id)
            
            # Exponential weighting: high scores có impact lớn hơn
            # Score 5 → 1.0, Score 4 → 0.5, Score 3 → 0, Score 2 → -0.5, Score 1 → -1.0
            if rating.score >= 3.0:
                weight = ((rating.score - 3.0) / 2.0) ** 1.5  # Emphasize high ratings
            else:
                weight = (rating.score - 3.0) / 2.0  # Linear for low ratings
            
            user_profile += weight * item_vec.toarray()[0]
            total_weight += abs(weight)
    
    # 2. XỬ LÝ LIKES (strong positive signal)
    LIKE_WEIGHT = 1.2
    
    for place_id in liked_place_ids:
        item_vec = get_item_vector(place_id)
        if item_vec is not None:
            interacted_places.add(place_id)
            user_profile += LIKE_WEIGHT * item_vec.toarray()[0]
            total_weight += LIKE_WEIGHT
    
    # 3. XỬ LÝ DISLIKES (strong negative signal)
    DISLIKE_WEIGHT = -1.0
    
    for place_id in disliked_place_ids:
        item_vec = get_item_vector(place_id)
        if item_vec is not None:
            interacted_places.add(place_id)
            user_profile += DISLIKE_WEIGHT * item_vec.toarray()[0]
            total_weight += abs(DISLIKE_WEIGHT)
            
    if total_weight == 0:
        return None, set(), set()
    
    # Normalize by total weight
    user_profile = user_profile / total_weight
        
    return user_profile, interacted_places, set(disliked_place_ids)

# 4. HÀM RECOMMEND CHÍNH (Content-Based + Item-Based CF + Popularity)
def recommend_content_based(user_prefs_tags, user_id: Optional[int] = None, top_k: int = 10):
    """
    Hàm gợi ý ĐƯỢC CẢI THIỆN với:
    1. TF-IDF thay vì Count Vectorizer
    2. Item-Based Collaborative Filtering
    3. Popularity Boost
    4. Better User Profile Building
    5. Diversity Optimization
    
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
    
    # Tạo vector từ tags (TF-IDF)
    try:
        query_vec = vectorizer.transform([search_query]).toarray()[0]
    except:
        query_vec = np.zeros(count_matrix.shape[1])

    # --- BƯỚC 2: KẾT HỢP VỚI LỊCH SỬ USER (NẾU CÓ) ---
    interacted_places = set()
    disliked_places = set()
    user_liked_places = []
    
    if user_id:
        user_profile_vec, interacted_places, disliked_places = build_user_profile(user_id)
        user_liked_places = get_user_likes(user_id)
        
        if user_profile_vec is not None:
            # HYBRID: 50% Current Intent + 50% User History (tăng weight history)
            final_vec = (query_vec * 0.5) + (user_profile_vec * 0.5)
        else:
            final_vec = query_vec
    else:
        final_vec = query_vec

    # --- BƯỚC 3: TÍNH CONTENT-BASED SCORES ---
    if np.all(final_vec == 0):
        # Cold-start: Không có prompt, không có history → POPULARITY-BASED
        results = items_df.copy()
        
        # Apply popularity scores
        if place_popularity:
            results['score'] = results['id'].apply(lambda x: place_popularity.get(x, 0.1))
        else:
            results['score'] = 0.5
        
        # Add diversity: mix popular with random
        results = results.sample(frac=1, random_state=None).reset_index(drop=True)
        results['score'] = results['score'] * np.random.uniform(0.8, 1.2, len(results))
    else:
        # Tính Cosine Similarity (Content-Based)
        content_scores = cosine_similarity([final_vec], count_matrix)[0]
        results = items_df.copy()
        results['content_score'] = content_scores
        
        # --- BƯỚC 4: THÊM ITEM-BASED COLLABORATIVE FILTERING ---
        cf_scores = np.zeros(len(results))
        
        if user_liked_places and item_similarity_matrix is not None:
            # Tính CF score dựa trên items user đã like
            for liked_place_id in user_liked_places[:10]:  # Top 10 liked items
                try:
                    liked_idx = items_df.index[items_df['id'] == liked_place_id].tolist()[0]
                    # Lấy similarity với tất cả items
                    cf_scores += item_similarity_matrix[liked_idx]
                except (IndexError, KeyError):
                    pass
            
            # Normalize CF scores
            if np.max(cf_scores) > 0:
                cf_scores = cf_scores / np.max(cf_scores)
        
        results['cf_score'] = cf_scores
        
        # --- BƯỚC 5: THÊM POPULARITY BOOST ---
        popularity_scores = np.zeros(len(results))
        if place_popularity:
            popularity_scores = results['id'].apply(lambda x: place_popularity.get(x, 0.0)).values
        
        results['popularity_score'] = popularity_scores
        
        # --- BƯỚC 6: KẾT HỢP CÁC SCORES (HYBRID) ---
        # Weights dựa trên có user history hay không
        if user_id and user_liked_places:
            # User có history: 40% content + 40% CF + 20% popularity
            results['score'] = (
                0.40 * results['content_score'] +
                0.40 * results['cf_score'] +
                0.20 * results['popularity_score']
            )
        else:
            # User mới: 60% content + 40% popularity
            results['score'] = (
                0.60 * results['content_score'] +
                0.40 * results['popularity_score']
            )
    
    # Thêm cột province (lấy từ tag đầu tiên)
    results['province'] = results['tags'].apply(lambda x: x[0] if x and len(x) > 0 else 'Vietnam')
    
    # --- BƯỚC 7: XỬ LÝ PLACES ĐÃ INTERACT (SOFT PENALTY) ---
    # Giảm score cho disliked places nhưng không loại bỏ hoàn toàn
    if disliked_places:
        # Penalty cho disliked places
        results.loc[results['id'].isin(disliked_places), 'score'] *= 0.1
    
    # Không filter interacted places trong evaluation
    # (để có thể recommend lại places user thích)
    
    # --- BƯỚC 8: LỌC THEO LOCATION (NẾU CÓ) ---
    # Tìm location tags từ user_prefs_tags (các tỉnh/thành phố Việt Nam)
    vietnam_locations = [
        'hanoi', 'ha noi', 'saigon', 'ho chi minh', 'danang', 'da nang', 
        'hue', 'nhatrang', 'nha trang', 'dalat', 'da lat', 'hoi an', 
        'phu quoc', 'sapa', 'sa pa', 'ninh binh', 'halong', 'ha long',
        'vung tau', 'can tho', 'quang ninh', 'lam dong', 'khanh hoa',
        'quang nam', 'thua thien hue', 'binh dinh', 'phu yen'
    ]
    
    location_tags = [
        tag for tag in user_prefs_tags 
        if any(loc in tag.lower() for loc in vietnam_locations)
    ]
    
    if location_tags:
        location_tags_lower = [loc.lower().strip() for loc in location_tags]
        
        def matches_location(tags_list):
            if not tags_list:
                return False
            tags_lower = [tag.lower() for tag in tags_list]
            return any(
                any(user_loc in tag for user_loc in location_tags_lower)
                for tag in tags_lower
            )
        
        # Boost places matching location thay vì filter cứng
        location_mask = results['tags'].apply(matches_location)
        results.loc[location_mask, 'score'] *= 1.5  # 50% boost for matching location
    
    # --- BƯỚC 9: DIVERSITY OPTIMIZATION ---
    # Sắp xếp theo score
    results = results.sort_values(by='score', ascending=False)
    
    # Lấy top candidates (3x top_k để có room cho diversity)
    candidates = results.head(top_k * 3)
    
    # Multi-dimension diversity: Đảm bảo đa dạng theo PROVINCE và CATEGORY riêng biệt
    selected = []
    province_count = Counter()  # Đếm số lần xuất hiện của mỗi province
    category_count = Counter()  # Đếm số lần xuất hiện của mỗi category
    
    # Giới hạn tối đa items từ cùng province hoặc category
    max_per_province = max(2, top_k // 3)  # Tối đa 1/3 từ cùng province
    max_per_category = max(3, top_k // 2)  # Tối đa 1/2 từ cùng category
    
    for _, row in candidates.iterrows():
        if len(selected) >= top_k:
            break
        
        place_tags = row['tags'] if isinstance(row['tags'], list) else []
        
        # Tag đầu tiên là province, các tag còn lại là categories
        province = place_tags[0] if len(place_tags) > 0 else 'Unknown'
        categories = place_tags[1:] if len(place_tags) > 1 else ['Unknown']
        
        # Kiểm tra điều kiện diversity
        province_ok = province_count[province] < max_per_province
        
        # Kiểm tra tất cả categories của place này
        category_ok = all(category_count[cat] < max_per_category for cat in categories)
        
        # Nếu đã chọn được 70% items, nới lỏng điều kiện để đảm bảo đủ số lượng
        relaxed_mode = len(selected) >= top_k * 0.7
        
        if province_ok and category_ok:
            selected.append(row)
            province_count[province] += 1
            for cat in categories:
                category_count[cat] += 1
        elif relaxed_mode and (province_ok or category_ok):
            # Relaxed mode: chỉ cần 1 trong 2 điều kiện
            selected.append(row)
            province_count[province] += 1
            for cat in categories:
                category_count[cat] += 1
    
    # Nếu không đủ, thêm các items còn lại theo score
    if len(selected) < top_k:
        remaining = candidates[~candidates.index.isin([r.name for r in selected])]
        selected.extend([row for _, row in remaining.head(top_k - len(selected)).iterrows()])
    
    # Convert back to DataFrame
    results = pd.DataFrame(selected)
    
    # Đảm bảo các cột cần thiết tồn tại
    results = results[['id', 'name', 'tags', 'province', 'score']].copy()
    
    return results.head(top_k)

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