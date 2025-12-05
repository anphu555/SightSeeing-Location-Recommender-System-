import google.generativeai as genai
import pandas as pd
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

# ---------------------------------------------------------
# 1. CẤU HÌNH API
# ---------------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY không tìm thấy trong file .env")
genai.configure(api_key=API_KEY)

# Sử dụng model Gemini 1.5 Flash để tối ưu tốc độ và chi phí
# Cấu hình response_mime_type="application/json" để ép model trả về JSON chuẩn
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

# CẤU HÌNH AN TOÀN TUYỆT ĐỐI
DELAY_SECONDS = 7       # 7 giây/request => ~8.5 RPM (Đảm bảo < 10 RPM)
DAILY_LIMIT = 240       # Dừng sau 240 request (Đảm bảo < 250 RPD)
INPUT_FILE = 'vietnam_tourism_data_cleaned.csv'
OUTPUT_FILE = 'vietnam_tourism_data_with_tags.csv'

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
# 3. HÀM MAIN - CHẠY VỚI CƠ CHẾ RESUME
# ---------------------------------------------------------
def main():
    # Bước 1: Load dữ liệu
    if not os.path.exists(INPUT_FILE):
        print(f"Lỗi: Không tìm thấy file {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    total_rows = len(df)
    
    # Bước 2: Kiểm tra file kết quả để resume (chạy tiếp)
    if os.path.exists(OUTPUT_FILE):
        print(f"Tìm thấy file kết quả cũ '{OUTPUT_FILE}'. Đang tải để chạy tiếp...")
        df_result = pd.read_csv(OUTPUT_FILE)
        # Đảm bảo cột tags tồn tại
        if 'tags' not in df_result.columns:
            df_result['tags'] = None
        # Merge với df gốc để đảm bảo có đầy đủ dữ liệu
        # Ưu tiên giữ tags từ df_result nếu đã có
        df_result = df.merge(df_result[['id', 'tags']], on='id', how='left', suffixes=('', '_old'))
        if 'tags_old' in df_result.columns:
            df_result['tags'] = df_result['tags_old']
            df_result = df_result.drop(columns=['tags_old'])
    else:
        print("Tạo file kết quả mới...")
        df_result = df.copy()
        df_result['tags'] = None # Khởi tạo cột tags rỗng

    # Bước 3: Xác định các dòng chưa có tags
    # Chỉ lấy các dòng mà cột 'tags' bị null (NaN)
    rows_to_process = df_result[df_result['tags'].isnull()]
    count_remaining = len(rows_to_process)
    
    print(f"Tổng số dòng: {total_rows}")
    print(f"Đã xử lý xong: {total_rows - count_remaining}")
    print(f"Còn lại: {count_remaining}")
    
    if count_remaining == 0:
        print("🎉 Chúc mừng! Bạn đã xử lý xong toàn bộ dữ liệu.")
        return

    print("-" * 40)
    print(f"🚀 Bắt đầu chạy batch hôm nay (Giới hạn: {DAILY_LIMIT} requests)...")
    print(f"⏳ Tốc độ: 1 request mỗi {DELAY_SECONDS} giây.")
    print(f"⏭️  Bắt đầu từ ID: {rows_to_process.iloc[0]['id']}")
    print("-" * 40)

    request_count = 0
    
    # Bước 4: Vòng lặp xử lý
    for index, row in rows_to_process.iterrows():
        # Kiểm tra giới hạn ngày
        if request_count >= DAILY_LIMIT:
            print(f"\n🛑 ĐÃ ĐẠT GIỚI HẠN {DAILY_LIMIT} REQUESTS HÔM NAY.")
            print("Hãy dừng lại và chạy tiếp code này vào ngày mai.")
            break

        print(f"[{request_count + 1}/{DAILY_LIMIT}] Processing ID {row['id']}: {row['name']}...", end=" ")
        
        # Gọi API
        tags = generate_tags_with_gemini(row['ai_input_text'])
        
        # Lưu kết quả vào DataFrame (đổi thành chuỗi JSON để lưu CSV)
        df_result.at[index, 'tags'] = json.dumps(tags)
        
        request_count += 1
        
        # In kết quả ngắn gọn
        if tags:
            print("✅ OK")
        else:
            print("⚠️ Empty")

        # Lưu file ngay sau mỗi 5 request để tránh mất điện/lỗi mạng
        if request_count % 5 == 0:
            df_result.to_csv(OUTPUT_FILE, index=False)
        
        # Sleep để đảm bảo RPM < 10
        time.sleep(DELAY_SECONDS)

    # Lưu lần cuối trước khi thoát
    df_result.to_csv(OUTPUT_FILE, index=False)
    print("\n" + "=" * 40)
    print(f"✅ Đã lưu tiến độ vào '{OUTPUT_FILE}'")
    print(f"📊 Hôm nay đã chạy: {request_count} dòng.")
    print(f"📉 Còn lại: {count_remaining - request_count} dòng.")
    
    if count_remaining - request_count > 0:
        print("👉 Hẹn gặp lại vào ngày mai!")
    else:
        print("🎉 Đã hoàn thành toàn bộ dataset!")

# ---------------------------------------------------------
# 4. CHẠY CHƯƠNG TRÌNH
# ---------------------------------------------------------
if __name__ == "__main__":
    main()