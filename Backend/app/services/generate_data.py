import pandas as pd
import sqlite3
import os
import numpy as np

# Cấu hình đường dẫn (tương ứng với cấu trúc folder của bạn)
# Bạn hãy đặt file này ở thư mục gốc của project hoặc điều chỉnh path cho phù hợp
BASE_DIR = os.getcwd() 
CSV_PATH = os.path.join(BASE_DIR, "Backend/app/services/vietnam_tourism_data_processed.csv")
DB_PATH = os.path.join(BASE_DIR, "Backend/travel_final.db")

# Đảm bảo thư mục tồn tại
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# --- PHẦN 1: TẠO DỮ LIỆU ĐỊA ĐIỂM (ITEMS) ---
# Dữ liệu mẫu đa dạng để test: Núi, Biển, Thành phố, Di sản
places_data = [
    # ID, Name, Province, Kind/Type, Weather, Lat, Lon
    (1, "Fansipan Legend", "Lao Cai", "mountain hiking scenery", "cold cloudy sunny", 22.3034, 103.7752),
    (2, "Ha Long Bay", "Quang Ninh", "beach island scenery heritage", "cool sunny", 20.9101, 107.1839),
    (3, "Trang An", "Ninh Binh", "river cave mountain heritage", "cool cloudy", 20.2506, 105.9744),
    (4, "My Khe Beach", "Da Nang", "beach sea swimming", "sunny warm", 16.0600, 108.2400),
    (5, "Hoi An Ancient Town", "Quang Nam", "culture history city", "warm sunny", 15.8801, 108.3380),
    (6, "Da Lat Market", "Lam Dong", "city food market", "cool cold", 11.9404, 108.4372),
    (7, "Langbiang Mountain", "Lam Dong", "mountain hiking nature", "cool cold windy", 12.0435, 108.4440),
    (8, "Phu Quoc Island", "Kien Giang", "island beach resort", "hot sunny", 10.2899, 103.9840),
    (9, "Phong Nha Ke Bang", "Quang Binh", "cave mountain nature heritage", "cool rainy", 17.5910, 106.2830),
    (10, "Ben Thanh Market", "Ho Chi Minh", "city market culture", "hot sunny", 10.7725, 106.6980),
    (11, "Imperial City Hue", "Thua Thien Hue", "history culture heritage", "hot rainy", 16.4637, 107.5960),
    (12, "Mui Ne Sand Dunes", "Binh Thuan", "desert beach sun", "hot sunny dry", 10.9333, 108.2833)
]

# Chuyển thành DataFrame cho CSV
df_csv = pd.DataFrame(places_data, columns=["id", "name", "province", "tourism_type", "weather_features", "lat", "lon"])

# Lưu file CSV cho RecSys Model (recsysmodel.py dùng file này)
# Lưu ý: recsysmodel.py cần các cột: id, name, province, tourism_type, weather_features
df_csv[["id", "name", "province", "tourism_type", "weather_features"]].to_csv(CSV_PATH, index=False)
print(f"[OK] Đã tạo file CSV tại: {CSV_PATH}")

# --- PHẦN 2: TẠO DATABASE SQLITE (sightseeing, users, ratings) ---

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 2.1 Tạo bảng sightseeing (cho db_service.py)
cursor.execute("DROP TABLE IF EXISTS sightseeing")
cursor.execute('''
    CREATE TABLE sightseeing (
        id INTEGER PRIMARY KEY,
        name TEXT,
        province TEXT,
        kind TEXT, -- Map từ tourism_type
        climate TEXT, -- Map từ weather_features
        lat REAL,
        lon REAL
    )
''')

# Insert dữ liệu địa điểm vào DB
for p in places_data:
    # p: (id, name, province, kind, weather, lat, lon)
    cursor.execute("INSERT INTO sightseeing (id, name, province, kind, climate, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?)", p)

# 2.2 Tạo bảng users và ratings
cursor.execute("DROP TABLE IF EXISTS ratings")
cursor.execute("DROP TABLE IF EXISTS users")

# Bảng users
cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    )
''')

# Bảng ratings
cursor.execute('''
    CREATE TABLE ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        place_id INTEGER NOT NULL,
        rating INTEGER NOT NULL, -- 1: Like, -1: Dislike, 0: None
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(username) REFERENCES users(username),
        FOREIGN KEY(place_id) REFERENCES sightseeing(id)
    )
''')

# --- PHẦN 3: TẠO DỮ LIỆU USER & RATING GIẢ LẬP (MOCK DATA) ---
# Mục đích: Test xem thuật toán có gợi ý đúng sở thích không.

users_mock = [
    ("mountain_lover", "hashed_pass_123"), # Thích núi, ghét biển
    ("beach_lover", "hashed_pass_456"),    # Thích biển, ghét núi
    ("culture_fan", "hashed_pass_789")     # Thích văn hóa/phố cổ
]

cursor.executemany("INSERT INTO users (username, hashed_password) VALUES (?, ?)", users_mock)

# Tạo ratings
ratings_mock = [
    # mountain_lover: Thích Fansipan(1), Langbiang(7), Phong Nha(9). Ghét Phu Quoc(8)
    ("mountain_lover", 1, 1),
    ("mountain_lover", 7, 1),
    ("mountain_lover", 9, 1),
    ("mountain_lover", 8, -1),
    
    # beach_lover: Thích Ha Long(2), My Khe(4), Phu Quoc(8). Ghét Fansipan(1)
    ("beach_lover", 2, 1),
    ("beach_lover", 4, 1),
    ("beach_lover", 8, 1),
    ("beach_lover", 1, -1),
    
    # culture_fan: Thích Hoi An(5), Hue(11), Ben Thanh(10).
    ("culture_fan", 5, 1),
    ("culture_fan", 11, 1),
    ("culture_fan", 10, 1)
]

cursor.executemany("INSERT INTO ratings (username, place_id, rating) VALUES (?, ?, ?)", ratings_mock)

conn.commit()
conn.close()
print(f"[OK] Đã khởi tạo Database và Mock Data tại: {DB_PATH}")
print("Done! Hệ thống đã sẵn sàng để test.")