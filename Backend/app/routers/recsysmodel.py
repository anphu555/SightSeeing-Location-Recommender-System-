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

# Đường dẫn đến file model và data
MODEL_PATH = 'app/routers/two_tower_model.keras' # Đường dẫn từ thư mục Backend
MLB_PATH = 'app/routers/mlb_vocab.pkl'           # Đường dẫn từ thư mục Backend
PLACES_CSV_PATH = 'app/services/vietnam_tourism_data_200tags.csv' # File csv chứa places

# Biến toàn cục để lưu model đã load
loaded_model = None
loaded_mlb = None
item_vectors = None
places_df = None

def load_resources():
    """Hàm này nên được gọi 1 lần khi start server (trong main.py lifespan)"""
    global loaded_model, loaded_mlb, item_vectors, places_df
    
    if loaded_model is None:
        print("Loading Two-Tower Model...")
        loaded_model = tf.keras.models.load_model(MODEL_PATH)
        loaded_mlb = pickle.load(open(MLB_PATH, 'rb'))
        
        # Load places và pre-calculate item vectors
        places_df = pd.read_csv(PLACES_CSV_PATH)
        # Đảm bảo tags là list
        if isinstance(places_df['tags'].iloc[0], str):
            places_df['tags'] = places_df['tags'].apply(ast.literal_eval)
            
        # Convert sang dense array để tương thích với Keras
        item_vectors_raw = loaded_mlb.transform(places_df['tags'])
        # Kiểm tra nếu là sparse matrix thì convert, nếu không thì giữ nguyên
        if hasattr(item_vectors_raw, 'toarray'):
            item_vectors = item_vectors_raw.toarray()
        else:
            item_vectors = item_vectors_raw
        print("Model loaded successfully!")

def recommend_two_tower(user_tags_list: list, top_k=5):
    """
    Hàm gợi ý sử dụng logic từ testModel.py
    """
    # Đảm bảo resources đã load
    if loaded_model is None:
        load_resources()

    # 1. Chuyển đổi tags của user thành vector
    # user_tags_list ví dụ: ['Nature', 'Beach'] lấy từ User.preferences hoặc Chatbot extraction
    if not user_tags_list:
        # Nếu user không có tags nào, trả về ngẫu nhiên hoặc top trending
        results = places_df.head(top_k).copy()
        results['score'] = 3.0  # Default neutral score
        return results

    # Chuẩn hóa tags: viết hoa chữ cái đầu mỗi từ để khớp với vocabulary
    # Ví dụ: 'beach' -> 'Beach', 'local cuisine' -> 'Local Cuisine'
    normalized_tags = [tag.title() for tag in user_tags_list]
    
    # Convert user tags sang dense array
    user_vector_raw = loaded_mlb.transform([normalized_tags])
    # Kiểm tra nếu là sparse matrix thì convert, nếu không thì giữ nguyên
    if hasattr(user_vector_raw, 'toarray'):
        user_vector = user_vector_raw.toarray()
    else:
        user_vector = user_vector_raw
    
    # 2. Repeat user vector để khớp với số lượng item
    user_vectors_repeated = np.repeat(user_vector, len(item_vectors), axis=0)
    
    # 3. Dự đoán
    raw_scores = loaded_model.predict([user_vectors_repeated, item_vectors], verbose=0).flatten()
    
    # 4. Quy đổi về thang điểm (như trong testModel.py)
    star_scores = raw_scores * 4.0 + 1.0
    
    # 5. Lấy Top K
    top_indices = star_scores.argsort()[-top_k:][::-1]
    
    # 6. Format kết quả trả về DataFrame để khớp với code cũ
    results = places_df.iloc[top_indices].copy()
    results['score'] = star_scores[top_indices]
    
    return results










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