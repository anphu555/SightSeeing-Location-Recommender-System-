import pandas as pd
import json
import os

# 1. Đọc file dữ liệu gốc
input_file = 'vietnam_tourism_data_en.csv'
output_file = 'vietnam_tourism_data_cleaned.csv'

# Kiểm tra xem file gốc có tồn tại không
if not os.path.exists(input_file):
    print(f"LỖI: Không tìm thấy file '{input_file}'. Hãy đảm bảo file này nằm cùng thư mục với code.")
else:
    df = pd.read_csv(input_file)

    # 2. Hàm xử lý: Nối văn bản để train AI (loại bỏ ||| và link ảnh thừa)
    def clean_description_for_ai(text):
        if not isinstance(text, str):
            return ""
        # Tách các đoạn
        parts = text.split('|||')
        # Lọc bỏ link ảnh và khoảng trắng thừa
        clean_parts = [p.strip() for p in parts if not p.strip().startswith('http') and p.strip()]
        # Nối lại bằng dấu chấm để thành đoạn văn liền mạch
        return ". ".join(clean_parts)

    # 3. Hàm xử lý: Chuyển thành JSON List để lưu vào Database (cột description)
    def to_json_list_desc(text):
        if not isinstance(text, str):
            return json.dumps([]) # Trả về mảng rỗng []
        parts = text.split('|||')
        # Lọc text sạch
        clean_parts = [p.strip() for p in parts if not p.strip().startswith('http') and p.strip()]
        return json.dumps(clean_parts, ensure_ascii=False)

    # 4. Hàm xử lý: Chuyển thành JSON List để lưu vào Database (cột image)
    def to_json_list_image(text):
        if not isinstance(text, str):
            return json.dumps([])
        parts = text.split('|||')
        # Lọc lấy link ảnh
        clean_parts = [p.strip() for p in parts if p.strip()]
        return json.dumps(clean_parts, ensure_ascii=False)

    # Áp dụng các hàm trên
    print("Đang xử lý dữ liệu...")
    # Tạo cột input cho model AI
    df['ai_input_text'] = df['description'].apply(clean_description_for_ai)
    
    # Tạo cột format JSON cho SQLModel
    df['description_json'] = df['description'].apply(to_json_list_desc)
    df['image_json'] = df['image'].apply(to_json_list_image)
    
    # Đổi tên title -> name cho khớp schema
    df['name'] = df['title']

    # Chọn các cột cần thiết để xuất file
    final_df = df[['id', 'name', 'ai_input_text', 'description_json', 'image_json']]

    # Lưu ra file CSV mới
    final_df.to_csv(output_file, index=False)
    
    print("-" * 30)
    print(f"XONG! Đã tạo file mới: {output_file}")
    print(f"Tổng số dòng: {len(final_df)}")
    print("Bạn hãy kiểm tra thư mục chứa file code để thấy file CSV mới này.")