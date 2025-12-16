import time
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.routers.recsysmodel import load_places_from_db

# 1. Load dữ liệu thật
print("--- Loading Data ---")
df = load_places_from_db()
if df.empty:
    print("Không có dữ liệu để test")
    exit()

data_soup = df['soup'].tolist()

# 2. Hàm đo lường
def benchmark_model(model_name, vectorizer_class):
    start_time = time.time()
    
    # Khởi tạo và fit model
    vectorizer = vectorizer_class(stop_words='english', max_features=5000)
    matrix = vectorizer.fit_transform(data_soup)
    
    # Giả lập 1 query tìm kiếm (Ví dụ: tìm địa điểm có tag đầu tiên của hàng đầu tiên)
    test_query = df.iloc[0]['tags'][0] if df.iloc[0]['tags'] else "nature"
    query_vec = vectorizer.transform([test_query])
    
    # Tính similarity
    sim = cosine_similarity(query_vec, matrix)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Lấy Top 5 kết quả
    scores = sim[0]
    top_indices = scores.argsort()[-5:][::-1]
    
    print(f"\nMODEL: {model_name}")
    print(f"Time executed: {duration:.4f} seconds")
    print(f"Search Query: '{test_query}'")
    print("Top 3 Recommendations:")
    for idx in top_indices[:3]:
        print(f" - {df.iloc[idx]['name']} (Score: {scores[idx]:.4f})")
        
    return duration, scores

# 3. Chạy so sánh
print("\n--- BẮT ĐẦU BENCHMARK ---")

# Model 1: CountVectorizer (Của bạn)
time_cv, scores_cv = benchmark_model("CountVectorizer", CountVectorizer)

# Model 2: TfidfVectorizer (Đối thủ)
time_tfidf, scores_tfidf = benchmark_model("TF-IDF", TfidfVectorizer)

# 4. Phân tích sự khác biệt (Dành cho báo cáo)
# Tìm trường hợp mà TF-IDF đánh giá thấp các từ khóa quan trọng
diff = scores_cv - scores_tfidf
max_diff_idx = diff.argmax()
print(f"\n--- PHÂN TÍCH SỰ KHÁC BIỆT ---")
print(f"Địa điểm chênh lệch điểm số nhiều nhất: {df.iloc[max_diff_idx]['name']}")
print(f"CountVec Score: {scores_cv[max_diff_idx]:.4f} | TF-IDF Score: {scores_tfidf[max_diff_idx]:.4f}")
print("Nhận xét: Nếu CountVec Score > TF-IDF Score đáng kể, chứng tỏ TF-IDF đang bị phạt nặng do từ khóa xuất hiện quá nhiều (IDF thấp).")