import google.generativeai as genai
import pandas as pd
import json
import time
import os
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
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

# CẤU HÌNH
DELAY_SECONDS = 7
INPUT_FILE = 'vietnam_tourism_data_cleaned.csv'
OUTPUT_FILE = 'vietnam_tourism_data_with_tags.csv'

# DANH SÁCH ID CẦN XỬ LÝ
SPECIFIC_IDS = [238, 239, 240]  # <--- Thay đổi danh sách ID ở đây

# ---------------------------------------------------------
# 2. HÀM GỌI GEMINI ĐỂ SINH TAGS
# ---------------------------------------------------------
def generate_tags_with_gemini(description_text):
    if not isinstance(description_text, str) or len(description_text) < 10:
        return []

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
        response = model.generate_content(prompt)
        tags_list = json.loads(response.text)
        return tags_list
    except Exception as e:
        print(f"Lỗi khi sinh tags: {e}")
        return []

# ---------------------------------------------------------
# 3. HÀM MAIN - XỬ LÝ CÁC ID CỤ THỂ
# ---------------------------------------------------------
def main():
    # Bước 1: Load dữ liệu gốc
    if not os.path.exists(INPUT_FILE):
        print(f"Lỗi: Không tìm thấy file {INPUT_FILE}")
        return

    df_input = pd.read_csv(INPUT_FILE)
    
    # Bước 2: Load file kết quả
    if os.path.exists(OUTPUT_FILE):
        print(f"Load file kết quả '{OUTPUT_FILE}'...")
        df_result = pd.read_csv(OUTPUT_FILE)
    else:
        print(f"Không tìm thấy '{OUTPUT_FILE}', tạo mới từ input...")
        df_result = df_input.copy()
        df_result['tags'] = None

    # Bước 3: Lọc các ID cần xử lý
    rows_to_process = df_input[df_input['id'].isin(SPECIFIC_IDS)]
    
    if len(rows_to_process) == 0:
        print(f"Không tìm thấy ID nào trong danh sách {SPECIFIC_IDS}")
        return
    
    print(f"Tìm thấy {len(rows_to_process)} dòng cần xử lý:")
    print(rows_to_process[['id', 'name']].to_string(index=False))
    print("-" * 60)
    
    # Bước 4: Xử lý từng ID
    for idx, row in rows_to_process.iterrows():
        print(f"Processing ID {row['id']}: {row['name']}...", end=" ")
        
        # Gọi API
        tags = generate_tags_with_gemini(row['ai_input_text'])
        
        # Cập nhật vào df_result (tìm đúng index theo ID)
        result_idx = df_result[df_result['id'] == row['id']].index
        if len(result_idx) > 0:
            df_result.at[result_idx[0], 'tags'] = json.dumps(tags)
        
        # In kết quả
        if tags:
            print(f"✅ OK - {tags}")
        else:
            print("⚠️ Empty")
        
        # Sleep
        time.sleep(DELAY_SECONDS)
    
    # Bước 5: Lưu kết quả
    df_result.to_csv(OUTPUT_FILE, index=False)
    print("\n" + "=" * 60)
    print(f"✅ Đã cập nhật {len(rows_to_process)} dòng vào '{OUTPUT_FILE}'")
    print("=" * 60)

if __name__ == "__main__":
    main()
