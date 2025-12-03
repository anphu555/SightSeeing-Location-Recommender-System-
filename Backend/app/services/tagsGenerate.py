import google.generativeai as genai
import pandas as pd
import json
import time

# ---------------------------------------------------------
# 1. CẤU HÌNH API
# ---------------------------------------------------------
API_KEY = "AIzaSyArPMZdcyNXAJFqqRh_QRnenuyFaEe68tc"  # <--- Dán API Key của bạn vào đây
genai.configure(api_key=API_KEY)

# Sử dụng model Gemini 1.5 Flash để tối ưu tốc độ và chi phí
# Cấu hình response_mime_type="application/json" để ép model trả về JSON chuẩn
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

# ---------------------------------------------------------
# 2. HÀM GỌI GEMINI ĐỂ SINH TAGS
# ---------------------------------------------------------
def generate_tags_with_gemini(description_text):
    if not isinstance(description_text, str) or len(description_text) < 10:
        return []

    # Prompt chi tiết
    prompt = f"""
    You are a travel recommendation AI. 
    Analyze the following description of a place in Vietnam and generate a list of 5 to 10 tags.
    
    Requirements:
    1. Tags must be in English.
    2. Format: A JSON list of strings.
    3. Include 1-2 Category tags (e.g., "Historical", "Nature", "Religious").
    4. Include 3-5 Attribute tags (e.g., "Cave", "Pagoda", "Hiking", "Architecture", "Beach").
    5. Include 1-2 Vibe/Context tags (e.g., "Peaceful", "Sightseeing", "Family-friendly").
    
    Description:
    "{description_text}"
    
    Output format example: ["Historical", "Temple", "Hanoi", "Architecture", "Sightseeing"]
    """

    try:
        # Gọi API
        response = model.generate_content(prompt)
        
        # Parse kết quả từ JSON string sang Python List
        tags_list = json.loads(response.text)
        return tags_list
        
    except Exception as e:
        print(f"Lỗi khi sinh tags: {e}")
        return []

# ---------------------------------------------------------
# 3. CHẠY TRÊN DỮ LIỆU CỦA BẠN
# ---------------------------------------------------------
# Đọc file đã làm sạch
df = pd.read_csv('vietnam_tourism_data_cleaned.csv')

# --- TEST THỬ TRÊN 5 DÒNG ĐẦU TIÊN (để kiểm tra trước) ---
print("Đang test sinh tags cho 5 địa điểm đầu tiên...")
sample_df = df.head(5).copy()

# Áp dụng hàm (Có delay nhẹ để tránh lỗi Rate Limit nếu dùng bản Free)
tags_results = []
for index, row in sample_df.iterrows():
    print(f"Đang xử lý ID {row['id']}: {row['name']}...")
    tags = generate_tags_with_gemini(row['ai_input_text'])
    tags_results.append(json.dumps(tags)) # Lưu dạng string JSON để ghi vào CSV
    time.sleep(2) # Nghỉ 2 giây giữa mỗi lần gọi (quan trọng với Free Tier)

sample_df['tags'] = tags_results

# In kết quả kiểm tra
print("\n--- KẾT QUẢ MẪU ---")
print(sample_df[['name', 'tags']].head())

# ---------------------------------------------------------
# 4. (TÙY CHỌN) CHẠY CHO TOÀN BỘ FILE
# Uncomment (bỏ comment) phần dưới nếu bạn muốn chạy hết 900 dòng
# ---------------------------------------------------------
# print("\nĐang chạy toàn bộ dữ liệu (sẽ mất thời gian)...")
# all_tags = []
# for index, row in df.iterrows():
#     if index % 10 == 0: print(f"Đã xử lý {index} dòng...")
#     tags = generate_tags_with_gemini(row['ai_input_text'])
#     all_tags.append(json.dumps(tags))
#     time.sleep(4) # Tăng delay lên 4s nếu chạy số lượng lớn ở Free Tier (giới hạn 15 RPM)
# 
# df['tags'] = all_tags
# df.to_csv('vietnam_tourism_final_with_tags.csv', index=False)
# print("Hoàn tất! Đã lưu file vietnam_tourism_final_with_tags.csv")