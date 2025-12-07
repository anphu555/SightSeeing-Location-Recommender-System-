from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
import csv
import json

from app.database import get_session
from app.schemas import Place


CSV_URL = 'app/services/vietnam_tourism_data_200tags.csv'



# Cách gọi đúng cho generator
session_generator = get_session()
session = next(session_generator) # <--- Lấy session thật ra khỏi generator

# Mở file CSV
with open(CSV_URL, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    count = 0
    for row in reader:
        try:
            # Đọc các cột từ file CSV mới
            place_id = row['id']
            name = row['name']
            
            # Parse JSON strings từ CSV
            description_json = row['description_json']
            image_json = row['image_json']
            tags_str = row['tags']
            
            # Convert JSON strings thành Python lists
            desc_list = json.loads(description_json) if description_json else []
            image_list = json.loads(image_json) if image_json else []
            
            # Parse tags - có thể là JSON array hoặc string với dấu phẩy
            try:
                tags_list = json.loads(tags_str) if tags_str else []
            except:
                # Nếu tags là string với dấu phẩy, split nó
                tags_list = [tag.strip().strip("'") for tag in tags_str.split(',')] if tags_str else []

            # Làm sạch các list - loại bỏ string rỗng, "[]", whitespace
            desc_list = [d.strip() for d in desc_list if d and d.strip() and d.strip() != "[]"]
            image_list = [img.strip() for img in image_list if img and img.strip() and img.strip() != "[]"]
            tags_list = [tag.strip() for tag in tags_list if tag and tag.strip() and tag.strip() != "[]"]

            # Skip nếu không có image hoặc các field quan trọng trống
            if not image_list or image_list == [""] or image_list == []:
                print(f"Skipping {name} - no images")
                continue
            
            if not desc_list or desc_list == []:
                print(f"Skipping {name} - no description")
                continue
            
            if not tags_list or tags_list == []:
                print(f"Skipping {name} - no tags")
                continue

            # Tạo object Place
            place = Place(
                name=name,
                description=desc_list,
                image=image_list,  # Giữ nguyên thứ tự từ CSV
                tags=tags_list
            )

            session.merge(place)
            count += 1
            
            if count % 10 == 0:
                print(f"Đã xử lý {count} địa điểm...")
                
        except Exception as e:
            print(f"Lỗi khi xử lý dòng {row.get('id', 'unknown')}: {str(e)}")
            continue

session.commit()
print(f"✅ Đã import {count} địa điểm thành công!")