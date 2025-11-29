import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Database giả lập (như cũ)
items_df = pd.DataFrame([
    {"id": 0, "name": "Lầu Ông Hoàng", "kind": "castle", "province": "Bình Thuận", "climate": "warm"},
    {"id": 1, "name": "Tháp Po Sah Inư", "kind": "ruins", "province": "Bình Thuận", "climate": "warm"},
    {"id": 2, "name": "Vịnh Hạ Long", "kind": "island", "province": "Quảng Ninh", "climate": "cool"},
])

# 2. Tạo "Feature Soup" cho Item (Gộp tất cả đặc điểm thành 1 chuỗi văn bản)
def create_soup(x):
    return f"{x['kind']} {x['province']} {x['climate']} is_{x['kind']} is_{x['climate']}"

items_df['soup'] = items_df.apply(create_soup, axis=1)

# 3. Khởi tạo Vectorizer
count = CountVectorizer()
count_matrix = count.fit_transform(items_df['soup'])

# 4. Hàm Recommend thay thế
def recommend(user_prompt):
    # --- Bước 1: Lọc cứng (Hard Filtering) ---
    # Giữ lại logic lọc theo tỉnh nếu cần, hoặc để model tự lo
    
    # --- Bước 2: Tạo User Profile từ Prompt ---
    # Chuyển đổi prompt user thành chuỗi keywords tương ứng với soup của item
    user_keywords = []
    
    if user_prompt['type'] != 'unknown':
        user_keywords.append(user_prompt['type'])       # vd: "island"
        user_keywords.append(f"is_{user_prompt['type']}")
    
    if user_prompt['location']:
         for loc in user_prompt['location']:
            user_keywords.append(loc)                   # vd: "Quảng Ninh"
            
    if user_prompt['weather'] != 'unknown':
        user_keywords.append(user_prompt['weather'])    # vd: "cool"
        user_keywords.append(f"is_{user_prompt['weather']}")

    user_soup = " ".join(user_keywords)
    
    # --- Bước 3: Tính toán độ tương đồng ---
    # Biến đổi user profile thành vector cùng không gian với item
    try:
        user_vector = count.transform([user_soup])
    except:
        # Trường hợp từ khóa lạ chưa từng xuất hiện
        return []

    # Tính Cosine Similarity giữa User và TOÀN BỘ Items
    cosine_sim = cosine_similarity(user_vector, count_matrix)
    
    # --- Bước 4: Xếp hạng ---
    scores = cosine_sim[0]
    items_df['score'] = scores
    
    # Sắp xếp giảm dần
    results = items_df.sort_values(by='score', ascending=False)
    
    return results[results['score'] > 0] # Chỉ trả về kết quả có độ liên quan