"""
Script cập nhật tọa độ chính xác cho các địa điểm trong database.
Sử dụng Nominatim (OpenStreetMap) API để geocode từ tên địa điểm.

Cách chạy:
    cd Backend
    python update_place_coordinates.py
"""

import sqlite3
import requests
import time
import json
from urllib.parse import quote

DB_PATH = "vietnamtravel.db"

# ────────────────────────────────
# Nominatim Geocoding API
# ────────────────────────────────
def geocode_place(place_name, province=None):
    """
    Geocode địa điểm sử dụng Nominatim API.
    Trả về (lat, lon) hoặc (None, None) nếu không tìm thấy.
    """
    # Tạo query - thêm province và "Vietnam" để tăng độ chính xác
    if province:
        query = f"{place_name}, {province}, Vietnam"
    else:
        query = f"{place_name}, Vietnam"
    
    url = f"https://nominatim.openstreetmap.org/search?q={quote(query)}&format=json&limit=1"
    
    headers = {
        'User-Agent': 'VietnamTravelApp/1.0 (exsighting@example.com)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            return lat, lon
        else:
            return None, None
            
    except Exception as e:
        print(f"  Lỗi geocoding: {e}")
        return None, None


# ────────────────────────────────
# Tọa độ trung tâm các tỉnh (fallback)
# ────────────────────────────────
PROVINCE_COORDS = {
    "ha noi": (21.0285, 105.8542),
    "hà nội": (21.0285, 105.8542),
    "ho chi minh": (10.8231, 106.6297),
    "hồ chí minh": (10.8231, 106.6297),
    "ho chi minh city": (10.8231, 106.6297),
    "da nang": (16.0544, 108.2022),
    "đà nẵng": (16.0544, 108.2022),
    "hue": (16.4637, 107.5909),
    "huế": (16.4637, 107.5909),
    "quang ninh": (21.0064, 107.2925),
    "quảng ninh": (21.0064, 107.2925),
    "ha long": (20.9101, 107.1839),
    "hạ long": (20.9101, 107.1839),
    "ninh binh": (20.2510, 105.9744),
    "ninh bình": (20.2510, 105.9744),
    "sapa": (22.3402, 103.8448),
    "sa pa": (22.3402, 103.8448),
    "lao cai": (22.3380, 104.1487),
    "lào cai": (22.3380, 104.1487),
    "nha trang": (12.2388, 109.1967),
    "khanh hoa": (12.2388, 109.1967),
    "khánh hòa": (12.2388, 109.1967),
    "da lat": (11.9404, 108.4583),
    "đà lạt": (11.9404, 108.4583),
    "lam dong": (11.9404, 108.4583),
    "lâm đồng": (11.9404, 108.4583),
    "phu quoc": (10.2899, 103.9840),
    "phú quốc": (10.2899, 103.9840),
    "kien giang": (10.0125, 105.0809),
    "kiên giang": (10.0125, 105.0809),
    "can tho": (10.0452, 105.7469),
    "cần thơ": (10.0452, 105.7469),
    "vung tau": (10.3460, 107.0843),
    "vũng tàu": (10.3460, 107.0843),
    "ba ria vung tau": (10.5417, 107.2428),
    "bà rịa vũng tàu": (10.5417, 107.2428),
    "an giang": (10.3868, 105.4353),
    "binh thuan": (10.9282, 108.1021),
    "bình thuận": (10.9282, 108.1021),
    "phan thiet": (10.9282, 108.1021),
    "mui ne": (10.9333, 108.2833),
    "mũi né": (10.9333, 108.2833),
    "quang binh": (17.4694, 106.6222),
    "quảng bình": (17.4694, 106.6222),
    "quang nam": (15.5394, 108.0191),
    "quảng nam": (15.5394, 108.0191),
    "hoi an": (15.8801, 108.3380),
    "hội an": (15.8801, 108.3380),
    "thanh hoa": (19.8067, 105.7852),
    "thanh hóa": (19.8067, 105.7852),
    "nghe an": (18.6583, 105.6813),
    "nghệ an": (18.6583, 105.6813),
    "hai phong": (20.8449, 106.6881),
    "hải phòng": (20.8449, 106.6881),
    "bac giang": (21.2819, 106.1967),
    "bắc giang": (21.2819, 106.1967),
    "dong nai": (10.9645, 106.8561),
    "đồng nai": (10.9645, 106.8561),
    "binh duong": (11.0063, 106.6528),
    "bình dương": (11.0063, 106.6528),
    "tay ninh": (11.3351, 106.1098),
    "tây ninh": (11.3351, 106.1098),
}

def get_fallback_coords(province):
    """Lấy tọa độ fallback từ tên tỉnh"""
    if not province:
        return None, None
    
    province_lower = province.lower().strip()
    
    if province_lower in PROVINCE_COORDS:
        return PROVINCE_COORDS[province_lower]
    
    # Tìm partial match
    for key, coords in PROVINCE_COORDS.items():
        if key in province_lower or province_lower in key:
            return coords
    
    return None, None


# ────────────────────────────────
# Cập nhật database
# ────────────────────────────────
def update_coordinates():
    """Cập nhật tọa độ cho tất cả địa điểm"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lấy danh sách places
    cursor.execute("SELECT id, name, tags, lat, lon FROM place")
    places = cursor.fetchall()
    
    print(f"Tìm thấy {len(places)} địa điểm trong database")
    print("="*60)
    
    geocoded = 0
    fallback_used = 0
    failed = 0
    
    for place_id, name, tags_json, current_lat, current_lon in places:
        try:
            tags = json.loads(tags_json) if tags_json else []
        except:
            tags = []
        
        # Lấy province từ tags[0]
        province = tags[0] if tags else None
        
        print(f"[{place_id}] {name}", end="")
        
        # Geocode địa điểm
        lat, lon = geocode_place(name, province)
        
        if lat is not None:
            print(f" -> ({lat:.4f}, {lon:.4f}) ✓")
            geocoded += 1
        else:
            # Fallback: sử dụng tọa độ tỉnh
            lat, lon = get_fallback_coords(province)
            if lat is not None:
                print(f" -> Fallback to {province}: ({lat:.4f}, {lon:.4f})")
                fallback_used += 1
            else:
                print(f" -> Không tìm thấy tọa độ ✗")
                failed += 1
                continue
        
        # Update database
        cursor.execute("""
            UPDATE place 
            SET lat = ?, lon = ?
            WHERE id = ?
        """, (lat, lon, place_id))
        
        # Rate limiting cho Nominatim (1 request/giây)
        time.sleep(1.1)
    
    conn.commit()
    conn.close()
    
    print("="*60)
    print(f"\n=== KẾT QUẢ ===")
    print(f"Geocoded thành công: {geocoded} địa điểm")
    print(f"Sử dụng fallback: {fallback_used} địa điểm")
    print(f"Thất bại: {failed} địa điểm")


def update_sample(limit=20):
    """Cập nhật một số địa điểm mẫu để test"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lấy một số places đa dạng
    cursor.execute("""
        SELECT id, name, tags FROM place 
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))
    places = cursor.fetchall()
    
    print(f"Test geocoding {len(places)} địa điểm...")
    print("="*60)
    
    for place_id, name, tags_json in places:
        try:
            tags = json.loads(tags_json) if tags_json else []
        except:
            tags = []
        
        province = tags[0] if tags else None
        
        print(f"[{place_id}] {name} ({province})", end="")
        
        lat, lon = geocode_place(name, province)
        
        if lat is not None:
            print(f" -> ({lat:.4f}, {lon:.4f}) ✓")
            cursor.execute("UPDATE place SET lat = ?, lon = ? WHERE id = ?", (lat, lon, place_id))
        else:
            print(f" -> Không tìm thấy")
        
        time.sleep(1.1)
    
    conn.commit()
    conn.close()
    print("="*60)
    print("Hoàn thành!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("=== CẬP NHẬT TẤT CẢ TỌA ĐỘ ===")
        print("CẢNH BÁO: Quá trình này sẽ mất ~15-20 phút do rate limiting")
        confirm = input("Tiếp tục? (y/n): ")
        if confirm.lower() == 'y':
            update_coordinates()
    else:
        print("=== TEST GEOCODING (20 địa điểm mẫu) ===")
        update_sample(20)
        print("\nĐể cập nhật tất cả, chạy: python update_place_coordinates.py --all")
