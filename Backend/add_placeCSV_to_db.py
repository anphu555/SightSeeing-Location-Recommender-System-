from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
import csv

from app.database import get_session
from app.schemas import Place


CSV_URL = 'app/services/a.csv'



# Cách gọi đúng cho generator
session_generator = get_session()
session = next(session_generator) # <--- Lấy session thật ra khỏi generator

# Mở file CSV
with open(CSV_URL, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        id = row['id']
        title = row['title']
        # Xử lý tách chuỗi description
        # Ví dụ: "mô tả 1|||mô tả 2" -> ["mô tả 1", "mô tả 2"]
        raw_desc = row['description']
        desc_list = raw_desc.split('|||')

        image_links = row['image']

        # Skip no image place
        if image_links == "":
            continue

        image_list = image_links.split('|||')
        
        # Tạo object Place
        place = Place(
            id=id,
            name=title,
            description=desc_list, # SQLModel tự động handle việc convert sang JSON
            image=image_list
        )

        session.merge(place)

session.commit()
print("Đã import dữ liệu thành công!")