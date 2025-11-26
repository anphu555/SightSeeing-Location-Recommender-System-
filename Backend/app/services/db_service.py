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
    # Tạo bảng users nếu chưa có
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            hashed_password TEXT NOT NULL
        )
    ''')
    conn.commit()
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


