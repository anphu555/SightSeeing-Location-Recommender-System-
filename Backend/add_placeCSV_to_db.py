import csv
import ast
import sys
import os
import json  # Import thêm thư viện JSON

# Thêm thư mục hiện tại vào sys.path
sys.path.append(os.getcwd())
import json

from sqlmodel import Session, select, create_engine, SQLModel
from app.schemas import Place

# 1. Cấu hình Database
sqlite_file_name = "vietnamtravel.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

# 2. Đường dẫn file CSV
CSV_FILE_PATH = 'app/services/vietnam_tourism_data_200tags_with_province.csv'

# Tăng giới hạn bộ nhớ cho việc đọc file CSV (vì description_json rất dài)
csv.field_size_limit(sys.maxsize)

def create_db_and_tables():
    """Tạo bảng nếu chưa có"""
    SQLModel.metadata.create_all(engine)

def parse_list_field(field_data):
    """
    Hàm xử lý thông minh: hỗ trợ cả JSON chuẩn và Python list string
    """
    if not field_data:
        return []
    
    field_data = field_data.strip()
    if field_data == "" or field_data == "[]":
        return []

    # Cách 1: Thử parse bằng JSON (Chuẩn nhất)
    try:
        # Thay thế 2 dấu ngoặc kép "" thành 1 " nếu do lỗi CSV
        cleaned_json = field_data.replace('""', '"')
        return json.loads(cleaned_json)
    except json.JSONDecodeError:
        pass

    # Cách 2: Thử parse bằng Python Syntax (ast)
    try:
        parsed = ast.literal_eval(field_data)
        if isinstance(parsed, list):
            return parsed
        return [str(parsed)]
    except (ValueError, SyntaxError):
        pass

    # Cách 3: Fallback thủ công (tách dấu phẩy)
    if ',' in field_data:
        # Loại bỏ ngoặc vuông nếu có
        clean_text = field_data.replace('[', '').replace(']', '').replace("'", "").replace('"', "")
        return [x.strip() for x in clean_text.split(',') if x.strip()]
    
    return [field_data]

def import_csv_to_db():
    create_db_and_tables()
    
    print(f"🚀 Bắt đầu nạp dữ liệu từ: {CSV_FILE_PATH}")
    
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ LỖI: Không tìm thấy file CSV tại {CSV_FILE_PATH}")
        return

    with Session(engine) as session:
        try:
            with open(CSV_FILE_PATH, mode='r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Chuẩn hóa tên cột (xóa khoảng trắng thừa nếu có)
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                print(f"ℹ️  Các cột tìm thấy: {reader.fieldnames}")
                
                count_new = 0
                count_updated = 0
                count_missing_tags = 0 # Đếm số lượng mất tags
                
                for row in reader:
                    # 1. Lấy ID từ CSV (quan trọng để đồng bộ)
                    place_id = row.get('id') or row.get('Id') or row.get('ID')
                    if place_id:
                        try:
                            place_id = int(place_id)
                        except (ValueError, TypeError):
                            place_id = None
                    
                    # 2. Lấy tên
                    name = row.get('name') or row.get('Name') or row.get('Title')
                    if not name: continue

                    # 3. Xử lý Description
                    raw_desc = row.get('description_json') or row.get('Description', '')
                    description_list = parse_list_field(raw_desc)

                    # 4. Xử lý Image
                    raw_img = row.get('image_json') or row.get('Image', '')
                    image_list = parse_list_field(raw_img)

                    # 5. Xử lý Tags (Quan trọng)
                    # Thử lấy từ nhiều tên cột khác nhau để chắc chắn
                    raw_tags = row.get('tags') or row.get('Tags') or row.get('tag', '')
                    tags_list = parse_list_field(raw_tags)

                    # --- DEBUG: In ra cảnh báo nếu không có tags ---
                    if not tags_list:
                        # Chỉ in 5 lỗi đầu tiên để không làm rối màn hình
                        if count_missing_tags < 5: 
                            print(f"⚠️  Cảnh báo: Không tìm thấy tags cho '{name}'. Dữ liệu gốc: '{raw_tags}'")
                        count_missing_tags += 1

                    # 6. Lưu vào DB với ID từ CSV
                    if place_id:
                        # Kiểm tra theo ID
                        existing_place = session.exec(select(Place).where(Place.id == place_id)).first()
                    else:
                        # Fallback: kiểm tra theo tên
                        existing_place = session.exec(select(Place).where(Place.name == name)).first()
                    
                    if not existing_place:
                        new_place = Place(
                            id=place_id,  # Sử dụng ID từ CSV
                            name=name,
                            description=description_list,
                            image=image_list,
                            tags=tags_list
                        )
                        session.add(new_place)
                        count_new += 1
                    else:
                        existing_place.name = name
                        existing_place.description = description_list
                        existing_place.image = image_list
                        existing_place.tags = tags_list
                        session.add(existing_place)
                        count_updated += 1

                session.commit()
                print("-" * 30)
                print(f"✅ THÀNH CÔNG!")
                print(f"➕ Thêm mới: {count_new}")
                print(f"🔄 Cập nhật: {count_updated}")
                if count_missing_tags > 0:
                    print(f"⚠️  Tổng số địa điểm bị thiếu tags: {count_missing_tags}")
                    print("👉 Hãy kiểm tra lại file CSV ở các dòng báo lỗi phía trên.")
                else:
                    print("✨ Tất cả địa điểm đều có tags đầy đủ!")

        except Exception as e:
            print(f"❌ Có lỗi nghiêm trọng: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import_csv_to_db()