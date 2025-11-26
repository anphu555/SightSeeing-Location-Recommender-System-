# app/services/db_service.py
import sqlite3
from app.config import settings

def get_db_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Thêm hàm khởi tạo bảng Users ---
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Bảng Users (Đã có từ bước trước)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            hashed_password TEXT NOT NULL
        )
    ''')
    
    # --- MỚI: Bảng Ratings ---
    # Lưu ai (username) đánh giá cái gì (place_id) bao nhiêu điểm (rating)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            place_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users(username),
            FOREIGN KEY(place_id) REFERENCES sightseeing(id)
        )
    ''')
    conn.commit()
    conn.close()

# --- MỚI: Hàm thêm đánh giá ---
def add_user_rating(username: str, place_id: int, rating: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Kiểm tra xem user đã đánh giá địa điểm này chưa
        cursor.execute("SELECT id FROM ratings WHERE username = ? AND place_id = ?", (username, place_id))
        existing = cursor.fetchone()
        
        if existing:
            # Nếu có rồi thì cập nhật (Update)
            cursor.execute("UPDATE ratings SET rating = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?", (rating, existing['id']))
        else:
            # Nếu chưa thì thêm mới (Insert)
            cursor.execute("INSERT INTO ratings (username, place_id, rating) VALUES (?, ?, ?)", (username, place_id, rating))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving rating: {e}")
        return False
    finally:
        conn.close()
        
# --- Các hàm thao tác User ---
def create_user(username: str, hashed_password: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username đã tồn tại
    finally:
        conn.close()

def get_user_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_places():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Lấy dữ liệu
        cursor.execute("SELECT id, name, province, kind, lat, lon FROM sightseeing")
        rows = cursor.fetchall()
        
        # --- DEBUG: In ra số lượng dòng lấy được ---
        print(f"--- DEBUG DB: Lấy được {len(rows)} dòng từ database ---")
        
        results = []
        for row in rows:
            place = dict(row)
            
            # Chuẩn hóa dữ liệu
            # Xử lý trường hợp kind hoặc name bị None
            kind = (place.get("kind") or "").lower()
            name = (place.get("name") or "").lower()
            
            themes = []
            # Thêm kind gốc vào theme
            if kind:
                themes.append(kind)
            
            # --- LOGIC GÁN NHÃN (Sửa lại cho mạnh hơn) ---
            # Kiểm tra cả tiếng Anh (peak, mountain) và tiếng Việt (núi)
            if any(kw in kind for kw in ["peak", "mountain", "hill", "hiking"]) or \
               any(kw in name for kw in ["núi", "nui", "peak", "mountain"]):
                themes.append("mountain")
                
            if any(kw in kind for kw in ["beach", "sea", "island", "coast", "bay"]) or \
               any(kw in name for kw in ["biển", "đảo", "bãi", "vịnh", "hòn"]):
                themes.append("beach")
            
            if "hotel" in kind or "resort" in kind:
                themes.append("resort")

            place["themes"] = themes
            place["region"] = "Vietnam" 
            place["country"] = "Vietnam"
            
            results.append(place)
            
        # --- DEBUG: In thử 1 địa điểm đầu tiên để xem themes có nhận không ---
        if results:
            print(f"--- DEBUG ITEM 1: {results[0]['name']} - Themes: {results[0]['themes']}")
            
        return results
        
    except Exception as e:
        print(f"Lỗi đọc DB: {e}")
        return []
    finally:
        conn.close()


