import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Tắt warning CUDA
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force TensorFlow dùng CPU

import tensorflow as tf
import pickle
import pandas as pd
import numpy as np
import ast
import warnings

# Tắt cảnh báo sklearn version
warnings.filterwarnings('ignore', category=UserWarning)

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# Đảm bảo bạn đã có đủ 3 file pickle/keras này
MODEL_PATH = 'app/routers/two_tower_model.keras'
MLB_PATH = 'app/routers/mlb_vocab.pkl'
PROVINCE_MAP_PATH = 'app/routers/province_map.pkl' # <-- FILE MỚI
PLACES_CSV_PATH = 'app/services/vietnam_tourism_data_200tags_with_province.csv' # <-- Dùng file có province

# Biến toàn cục
loaded_model = None
loaded_mlb = None
loaded_province_map = None # <-- Biến mới
item_features_cache = None # Lưu cache (tags_vec, province_id) của tất cả items
places_df = None

def load_resources():
    """Hàm này nên được gọi 1 lần khi start server"""
    global loaded_model, loaded_mlb, loaded_province_map, item_features_cache, places_df
    
    if loaded_model is None:
        print("Loading Two-Tower Model System...")
        
        # 1. Load Model & Disctionaries
        try:
            loaded_model = tf.keras.models.load_model(MODEL_PATH)
            with open(MLB_PATH, 'rb') as f:
                loaded_mlb = pickle.load(f)
            with open(PROVINCE_MAP_PATH, 'rb') as f:
                loaded_province_map = pickle.load(f)
        except Exception as e:
            print(f"Lỗi khi load model/pickle: {e}")
            return

        # 2. Load Data Places
        places_df = pd.read_csv(PLACES_CSV_PATH)
        
        # 3. Pre-process Data (Tách Tỉnh & Tags giống hệt lúc Train)
        # Hàm parse tags
        def parse_and_split(x):
            try:
                tags = ast.literal_eval(x)
                if not tags: return "Unknown", []
                # Quy ước: Tag đầu tiên là Tỉnh
                return tags[0], tags[1:] 
            except:
                return "Unknown", []

        # Tách cột
        print("Processing Places Data...")
        places_df[['province', 'clean_tags']] = places_df['tags'].apply(
            lambda x: pd.Series(parse_and_split(x))
        )
        
        # 4. Tạo Cache Features cho toàn bộ Items (để predict cho nhanh)
        # a. Tags Vector (One-hot)
        all_item_tags_vec = loaded_mlb.transform(places_df['clean_tags'])
        
        # b. Province Index
        # Map tên tỉnh sang ID. Nếu tỉnh mới lạ ko có trong map thì gán 0
        all_item_prov_idx = places_df['province'].apply(
            lambda x: loaded_province_map.get(x, 0)
        ).values
        
        # Lưu vào cache để dùng cho hàm predict
        item_features_cache = {
            'item_tags_input': all_item_tags_vec,
            'item_province_input': all_item_prov_idx
        }
        
        print("✅ Load Resources Complete!")

def get_recommendations(user_prefs_tags, top_k=10):
    """
    Hàm gợi ý cho 1 user dựa trên tags sở thích.
    Args:
        user_prefs_tags (list): List các tags user thích (VD: ['Nature', 'Cave'])
    """
    global loaded_model, loaded_mlb, item_features_cache, places_df
    
    if loaded_model is None:
        load_resources()
        
    # 1. Chuẩn bị Input cho User Tower
    # Biến đổi tags user nhập vào thành vector
    user_vec = loaded_mlb.transform([user_prefs_tags]) # Shape (1, num_features)
    
    # Lặp lại vector user cho bằng số lượng items để đưa vào model
    num_items = len(places_df)
    user_vec_repeated = np.repeat(user_vec, num_items, axis=0)
    
    # 2. Dự đoán (Batch Predict)
    # Input dictionary phải đúng tên layer trong model
    inputs = {
        'user_input': user_vec_repeated,
        'item_tags_input': item_features_cache['item_tags_input'],
        'item_province_input': item_features_cache['item_province_input']
    }
    
    predictions = loaded_model.predict(inputs, batch_size=512, verbose=0)
    
    # 3. Lấy kết quả
    scores = predictions.flatten()
    
    # Tạo bảng kết quả tạm
    results = places_df.copy()
    results['score'] = scores
    
    # Sort và lấy top K
    top_results = results.sort_values(by='score', ascending=False).head(top_k)
    
    # Trả về các trường cần thiết (json)
    return top_results[['id', 'name', 'province', 'score']].to_dict(orient='records')

def recommend_two_tower(user_prefs_tags, top_k=10):
    """
    Wrapper function for get_recommendations to match the import name.
    Returns a DataFrame instead of dict for compatibility with recommendation.py
    
    Args:
        user_prefs_tags (list): List các tags user thích
        top_k (int): Số lượng gợi ý trả về
    
    Returns:
        pd.DataFrame: DataFrame chứa các địa điểm được gợi ý
    """
    global loaded_model, loaded_mlb, item_features_cache, places_df
    
    if loaded_model is None:
        load_resources()
    
    # MAPPING: Từ user input thông thường sang tags trong vocabulary
    # Vì MLB vocabulary chứa các tags cụ thể từ dataset
    tag_mapping = {
        'beach': ['Beach', 'Coastal', 'Sea', 'Island', 'Ocean'],
        'mountain': ['Mountain', 'Highland', 'Hill', 'Trekking', 'Hiking'],
        'nature': ['Nature', 'Natural', 'Ecotourism', 'Wildlife'],
        'historical': ['Historical', 'History', 'Heritage', 'Cultural Heritage'],
        'temple': ['Temple', 'Pagoda', 'Religious', 'Spiritual'],
        'city': ['City', 'Urban', 'Modern'],
        'food': ['Cuisine', 'Food', 'Restaurant'],
        'adventure': ['Adventure', 'Outdoor', 'Sports'],
        'relaxing': ['Relaxing', 'Peaceful', 'Quiet'],
        'festival': ['Festival', 'Event', 'Celebration']
    }
    
    # Expand user tags với mapping
    expanded_tags = []
    vocab_set = set(loaded_mlb.classes_)
    
    for tag in user_prefs_tags:
        tag_lower = tag.lower()
        
        # 1. Thử tag gốc (capitalize)
        if tag in vocab_set:
            expanded_tags.append(tag)
        elif tag.capitalize() in vocab_set:
            expanded_tags.append(tag.capitalize())
        
        # 2. Thử mapping
        if tag_lower in tag_mapping:
            for mapped_tag in tag_mapping[tag_lower]:
                if mapped_tag in vocab_set:
                    expanded_tags.append(mapped_tag)
    
    # Nếu không match được gì, dùng tags phổ biến
    if not expanded_tags:
        print(f"⚠️ Warning: Tags {user_prefs_tags} not found in vocabulary. Using default.")
        expanded_tags = ['Vietnam', 'Sightseeing', 'Cultural']
    
    print(f"🔍 User input: {user_prefs_tags} → Expanded: {expanded_tags}")
        
    # 1. Chuẩn bị Input cho User Tower
    user_vec = loaded_mlb.transform([expanded_tags])
    
    # 2. Lặp lại vector user cho bằng số lượng items
    num_items = len(places_df)
    user_vec_repeated = np.repeat(user_vec, num_items, axis=0)
    
    # 3. Dự đoán
    inputs = {
        'user_input': user_vec_repeated,
        'item_tags_input': item_features_cache['item_tags_input'],
        'item_province_input': item_features_cache['item_province_input']
    }
    
    predictions = loaded_model.predict(inputs, batch_size=512, verbose=0)
    
    # 4. Lấy kết quả
    scores = predictions.flatten()
    
    # Tạo DataFrame kết quả
    results = places_df.copy()
    results['score'] = scores
    
    # Sort và lấy top K
    top_results = results.sort_values(by='score', ascending=False).head(top_k)
    
    # Parse tags từ string sang list trước khi trả về
    def safe_parse_tags(x):
        if isinstance(x, str):
            try:
                return ast.literal_eval(x)
            except:
                return []
        elif isinstance(x, list):
            return x
        else:
            return []
    
    # Tạo bản copy và parse tags
    final_results = top_results.copy()
    final_results['tags'] = final_results['tags'].apply(safe_parse_tags)
    
    # Trả về DataFrame (không phải dict)
    return final_results[['id', 'name', 'tags', 'province', 'score']]

# --- TEST CODE (Chạy thử khi execute file này) ---
if __name__ == "__main__":
    load_resources()
    
    # Giả lập user thích đi Chùa & Lễ hội
    demo_tags = ['Temple', 'Festival', 'Historical']
    print(f"\nUser thích: {demo_tags}")
    
    recs = get_recommendations(demo_tags)
    for r in recs:
        print(f"- [{r['province']}] {r['name']} (Score: {r['score']:.2f})")









# import pandas as pd
# import numpy as np
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from sqlmodel import Session, select
# from typing import Optional

# from app.schemas import Place, Rating
# from app.database import engine

# # ==========================================
# # 1. LOAD DỮ LIỆU TỪ DATABASE.DB
# # ==========================================

# def load_places_from_db():
#     """Load tất cả places từ database.db vào DataFrame"""
#     with Session(engine) as session:
#         statement = select(Place)
#         places = session.exec(statement).all()
        
#         # Chuyển đổi sang list of dict
#         places_data = []
#         for place in places:
#             # Kết hợp các fields thành text để vectorize
#             # tags là List[str], description cũng là List[str]
#             tags_text = " ".join(place.tags) if place.tags else ""
#             desc_text = " ".join(place.description) if place.description else ""
            
#             places_data.append({
#                 "id": place.id,
#                 "name": place.name,
#                 "tags": place.tags,
#                 "description": place.description,
#                 "images": place.image,
#                 # Tạo soup để vectorize
#                 "soup": f"{place.name} {tags_text} {desc_text}"
#             })
        
#         return pd.DataFrame(places_data)

# # LAZY LOADING: Chỉ load khi cần, không load ngay khi import module
# items_df = None
# count_matrix = None
# vectorizer = None

# def initialize_recsys():
#     """Khởi tạo RecSys model - gọi hàm này sau khi database đã được tạo"""
#     global items_df, count_matrix, vectorizer
    
#     if items_df is not None:
#         return  # Đã khởi tạo rồi
    
#     try:
#         # Load data từ database
#         items_df = load_places_from_db()
        
#         if len(items_df) == 0:
#             print("Warning: No places found in database")
#             return
        
#         # Khởi tạo vectorizer
#         vectorizer = CountVectorizer(stop_words='english', max_features=5000)
#         count_matrix = vectorizer.fit_transform(items_df['soup'])
        
#         print(f"RecSys initialized with {len(items_df)} places")
#     except Exception as e:
#         print(f"Failed to initialize RecSys: {e}")
#         items_df = pd.DataFrame()  # Empty dataframe để tránh lỗi

# # --- HÀM HỖ TRỢ ---

# def get_item_vector(item_id):
#     """Lấy vector của một địa điểm dựa trên ID"""
#     if count_matrix is None:
#         return None
#     try:
#         idx = items_df.index[items_df['id'] == item_id].tolist()[0]
#         return count_matrix[idx]
#     except (IndexError, KeyError):
#         return None

# def build_user_profile(user_id: int):
#     """
#     Tạo vector sở thích người dùng dựa trên Rating history
#     Score cao (4-5) → Positive influence
#     Score thấp (1-2) → Negative influence
#     """
#     with Session(engine) as session:
#         statement = select(Rating).where(Rating.user_id == user_id)
#         ratings = session.exec(statement).all()
        
#         if not ratings:
#             return None  # User mới hoàn toàn (Cold start)

#     # Khởi tạo vector rỗng
#     if count_matrix is None:
#         return None
        
#     user_profile = np.zeros(count_matrix.shape[1])
#     interaction_count = 0
    
#     for rating in ratings:
#         item_vec = get_item_vector(rating.place_id)
#         if item_vec is not None:
#             # Chuyển đổi score (1-5) thành weight (-1 đến +1)
#             # Score 5 → +1, Score 3 → 0, Score 1 → -1
#             weight = (rating.score - 3.0) / 2.0  # Normalize về [-1, 1]
            
#             user_profile += weight * item_vec.toarray()[0]
#             interaction_count += 1
            
#     if interaction_count == 0:
#         return None
        
#     return user_profile

# # 4. HÀM RECOMMEND CHÍNH
# def recommend(user_prompt_extraction, user_id: Optional[int] = None):
#     """
#     user_prompt_extraction: Kết quả JSON từ LLM (user_text)
#     user_id: ID người dùng để lấy lịch sử ratings
#     """
#     # Đảm bảo RecSys đã được khởi tạo
#     initialize_recsys()
    
#     if count_matrix is None or items_df is None or len(items_df) == 0:
#         return pd.DataFrame()  # Return empty dataframe
    
#     # --- BƯỚC 1: XÂY DỰNG QUERY VECTOR TỪ PROMPT ---
#     search_keywords = []
    
#     # Lấy thông tin từ extraction
#     if user_prompt_extraction.type and user_prompt_extraction.type != 'unknown':
#         search_keywords.append(user_prompt_extraction.type)
        
#     for loc in user_prompt_extraction.location:
#         search_keywords.append(loc)
        
#     if user_prompt_extraction.weather and user_prompt_extraction.weather != 'unknown':
#         search_keywords.append(user_prompt_extraction.weather)

#     search_query = " ".join(search_keywords)
    
#     # Tạo vector từ prompt
#     try:
#         query_vec = vectorizer.transform([search_query]).toarray()[0]
#     except:
#         query_vec = np.zeros(count_matrix.shape[1])

#     # --- BƯỚC 2: KẾT HỢP VỚI LỊCH SỬ USER (NẾU CÓ) ---
#     if user_id:
#         user_profile_vec = build_user_profile(user_id)
#         if user_profile_vec is not None:
#             # HYBRID: 70% Prompt + 30% User History
#             final_vec = (query_vec * 0.7) + (user_profile_vec * 0.3)
#         else:
#             final_vec = query_vec
#     else:
#         final_vec = query_vec

#     # --- BƯỚC 3: TÍNH TOÁN ---
#     if np.all(final_vec == 0):
#         # Không có prompt, không có history → Trả về top items
#         results = items_df.copy()
#         results['score'] = 0.5  # Default score
#         return results.head(10)

#     # Tính Cosine Similarity
#     cosine_sim = cosine_similarity([final_vec], count_matrix)
#     scores = cosine_sim[0]
    
#     # Tạo bảng kết quả
#     results = items_df.copy()
#     results['score'] = scores
    
#     # --- BƯỚC 4: LỌC THEO LOCATION (NẾU CÓ) ---
#     # Note: Schema mới không có trường 'province', chỉ có 'tags'
#     # Bạn có thể lọc theo tags nếu tags chứa tên địa danh
#     if user_prompt_extraction.location:
#         user_locations_lower = [loc.lower().strip() for loc in user_prompt_extraction.location]
        
#         def matches_location(tags_list):
#             if not tags_list:
#                 return False
#             tags_lower = [tag.lower() for tag in tags_list]
#             return any(
#                 any(user_loc in tag for user_loc in user_locations_lower)
#                 for tag in tags_lower
#             )
        
#         # Filter places có tags chứa location
#         mask = results['tags'].apply(matches_location)
#         filtered = results[mask]
        
#         # Nếu filter quá chặt (không còn kết quả), giữ nguyên
#         if len(filtered) > 0:
#             results = filtered

#     # Sắp xếp giảm dần theo score
#     results = results.sort_values(by='score', ascending=False)
    
#     return results