import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from app.services.db_service import get_user_ratings_map # Hàm này bạn đã có

# 1. LOAD DỮ LIỆU THẬT
# Đường dẫn đến file CSV đã xử lý của bạn
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "services", "vietnam_tourism_data_processed.csv")

try:
    items_df = pd.read_csv(CSV_PATH)
    # Xử lý lấp đầy dữ liệu trống nếu cần
    items_df.fillna('', inplace=True)
except Exception as e:
    print(f"Error loading data: {e}")
    # Fallback nếu lỗi (để code không crash khi test)
    items_df = pd.DataFrame(columns=['id', 'name', 'province', 'tourism_type', 'weather_features'])

# 2. TẠO FEATURE SOUP (TRỘN DATA)
def create_soup(x):
    # Kết hợp các đặc trưng quan trọng để Vectorizer học
    # Giả sử cột trong CSV là: 'tourism_type', 'province', 'weather_features'
    # Bạn kiểm tra lại tên cột trong CSV nhé
    return f"{x.get('tourism_type', '')} {x.get('province', '')} {x.get('weather_features', '')}"

items_df['soup'] = items_df.apply(create_soup, axis=1)

# 3. KHỞI TẠO MODEL (CountVectorizer)
# Dùng max_features để giới hạn số lượng từ vựng quan trọng nhất, tránh quá nặng
vectorizer = CountVectorizer(stop_words='english', max_features=5000)
try:
    count_matrix = vectorizer.fit_transform(items_df['soup'])
except ValueError:
    print("Not enough data to fit vectorizer")
    count_matrix = None

# --- HÀM HỖ TRỢ ---

def get_item_vector(item_id):
    """Lấy vector của một địa điểm dựa trên ID"""
    try:
        idx = items_df.index[items_df['id'] == item_id].tolist()[0]
        return count_matrix[idx]
    except IndexError:
        return None

def build_user_profile(username: str):
    """
    Tạo vector sở thích người dùng dựa trên Like/Dislike
    Like (+1), Dislike (-1)
    """
    # Lấy map {place_id: score} từ DB (ví dụ: {10: 1, 15: -1})
    ratings_map = get_user_ratings_map(username) 
    
    if not ratings_map:
        return None # User mới hoàn toàn (Cold start)

    # Khởi tạo vector rỗng (cùng kích thước với vector địa điểm)
    user_profile = np.zeros(count_matrix.shape[1])
    
    interaction_count = 0
    
    for place_id, score in ratings_map.items():
        item_vec = get_item_vector(int(place_id))
        if item_vec is not None:
            # ROCCHIO ALGORITHM CƠ BẢN:
            # Cộng vector địa điểm thích, Trừ vector địa điểm ghét
            # score là 1 (Like) hoặc -1 (Dislike)
            user_profile += score * item_vec.toarray()[0]
            interaction_count += 1
            
    if interaction_count == 0:
        return None
        
    return user_profile

# 4. HÀM RECOMMEND CHÍNH
def recommend(user_prompt_extraction, username: str = None):
    """
    user_prompt_extraction: Kết quả JSON từ LLM (user_text)
    username: Tên người dùng để lấy lịch sử
    """
    
    # --- BƯỚC 1: XÂY DỰNG QUERY VECTOR TỪ PROMPT ---
    # Biến đổi prompt của user thành keywords
    search_keywords = []
    
    # Lấy thông tin từ extraction (JSON từ file llm_service)
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
    if username:
        user_profile_vec = build_user_profile(username)
        if user_profile_vec is not None:
            # HYBRID: Tổng hợp nhu cầu hiện tại (Prompt) + Sở thích quá khứ (History)
            # Bạn có thể nhân trọng số (weight) nếu muốn ưu tiên cái nào hơn
            # Ví dụ: 0.7 * Prompt + 0.3 * History
            final_vec = (query_vec * 0.7) + (user_profile_vec * 0.3)
        else:
            final_vec = query_vec
    else:
        final_vec = query_vec

    # --- BƯỚC 3: TÍNH TOÁN VÀ LỌC ---
    # Nếu vector toàn số 0 (không có prompt, không có history) -> Trả về random hoặc top rate
    if np.all(final_vec == 0):
        return items_df.head(10) # Hoặc logic "Trending"

    # Tính Cosine Similarity giữa Final Vector và tất cả Items
    # Reshape final_vec để tương thích với cosine_similarity
    cosine_sim = cosine_similarity([final_vec], count_matrix)
    
    # Lấy điểm số
    scores = cosine_sim[0]
    
    # Tạo bảng kết quả tạm
    results = items_df.copy()
    results['score'] = scores
    
    # --- BƯỚC 4: LỌC CỨNG (Hard Filter) ---
    # Nếu user chỉ định rõ tỉnh thành, ta lọc bớt các tỉnh không liên quan
    if user_prompt_extraction.location:
        # Chuẩn hóa: lowercase và loại bỏ khoảng trắng thừa để so sánh tốt hơn
        def normalize_location(s):
            if pd.isna(s):
                return ""
            return str(s).lower().strip()
        
        # Chuẩn hóa danh sách location từ user
        user_locations = [normalize_location(loc) for loc in user_prompt_extraction.location]
        
        # Lọc những nơi có province chứa bất kỳ location nào user yêu cầu
        results = results[
            results['province'].apply(
                lambda x: any(user_loc in normalize_location(x) for user_loc in user_locations)
            )
        ]

    # Sắp xếp giảm dần theo điểm
    results = results.sort_values(by='score', ascending=False)
    
    return results