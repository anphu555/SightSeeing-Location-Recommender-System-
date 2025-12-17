"""
Script cập nhật dữ liệu climate (thời tiết) cho các địa điểm trong database.
Sử dụng Open-Meteo API để lấy nhiệt độ hiện tại và phân loại khí hậu.

Cách chạy:
    cd Backend
    python update_climate_data.py
"""

import sqlite3
import requests
import time
import json

DB_PATH = "vietnamtravel.db"

# ────────────────────────────────
# Tọa độ trung tâm các tỉnh/thành phố Việt Nam
# ────────────────────────────────
PROVINCE_COORDS = {
    # Miền Bắc
    "ha noi": (21.0285, 105.8542),
    "hà nội": (21.0285, 105.8542),
    "hanoi": (21.0285, 105.8542),
    "ha giang": (22.8233, 104.9838),
    "hà giang": (22.8233, 104.9838),
    "cao bang": (22.6666, 106.2580),
    "cao bằng": (22.6666, 106.2580),
    "bac kan": (22.1471, 105.8347),
    "bắc kạn": (22.1471, 105.8347),
    "tuyen quang": (21.8230, 105.2140),
    "tuyên quang": (21.8230, 105.2140),
    "lao cai": (22.3380, 104.1487),
    "lào cai": (22.3380, 104.1487),
    "sapa": (22.3402, 103.8448),
    "sa pa": (22.3402, 103.8448),
    "dien bien": (21.3867, 103.0230),
    "điện biên": (21.3867, 103.0230),
    "lai chau": (22.3860, 103.4594),
    "lai châu": (22.3860, 103.4594),
    "son la": (21.3269, 103.9144),
    "sơn la": (21.3269, 103.9144),
    "yen bai": (21.7236, 104.9113),
    "yên bái": (21.7236, 104.9113),
    "hoa binh": (20.8169, 105.3381),
    "hòa bình": (20.8169, 105.3381),
    "thai nguyen": (21.5928, 105.8442),
    "thái nguyên": (21.5928, 105.8442),
    "lang son": (21.8537, 106.7613),
    "lạng sơn": (21.8537, 106.7613),
    "quang ninh": (21.0064, 107.2925),
    "quảng ninh": (21.0064, 107.2925),
    "ha long": (20.9101, 107.1839),
    "hạ long": (20.9101, 107.1839),
    "bac giang": (21.2819, 106.1967),
    "bắc giang": (21.2819, 106.1967),
    "phu tho": (21.3229, 105.2016),
    "phú thọ": (21.3229, 105.2016),
    "vinh phuc": (21.3609, 105.5474),
    "vĩnh phúc": (21.3609, 105.5474),
    "bac ninh": (21.1214, 106.1111),
    "bắc ninh": (21.1214, 106.1111),
    "hai duong": (20.9374, 106.3146),
    "hải dương": (20.9374, 106.3146),
    "hai phong": (20.8449, 106.6881),
    "hải phòng": (20.8449, 106.6881),
    "hung yen": (20.6464, 106.0511),
    "hưng yên": (20.6464, 106.0511),
    "thai binh": (20.4463, 106.3422),
    "thái bình": (20.4463, 106.3422),
    "ha nam": (20.5835, 105.9230),
    "hà nam": (20.5835, 105.9230),
    "nam dinh": (20.4200, 106.1683),
    "nam định": (20.4200, 106.1683),
    "ninh binh": (20.2510, 105.9744),
    "ninh bình": (20.2510, 105.9744),
    
    # Miền Trung
    "thanh hoa": (19.8067, 105.7852),
    "thanh hóa": (19.8067, 105.7852),
    "nghe an": (18.6583, 105.6813),
    "nghệ an": (18.6583, 105.6813),
    "ha tinh": (18.3559, 105.8877),
    "hà tĩnh": (18.3559, 105.8877),
    "quang binh": (17.4694, 106.6222),
    "quảng bình": (17.4694, 106.6222),
    "quang tri": (16.7579, 107.1856),
    "quảng trị": (16.7579, 107.1856),
    "thua thien hue": (16.4674, 107.5905),
    "thừa thiên huế": (16.4674, 107.5905),
    "hue": (16.4637, 107.5909),
    "huế": (16.4637, 107.5909),
    "da nang": (16.0544, 108.2022),
    "đà nẵng": (16.0544, 108.2022),
    "quang nam": (15.5394, 108.0191),
    "quảng nam": (15.5394, 108.0191),
    "hoi an": (15.8801, 108.3380),
    "hội an": (15.8801, 108.3380),
    "quang ngai": (15.1205, 108.8042),
    "quảng ngãi": (15.1205, 108.8042),
    "binh dinh": (13.7830, 109.2197),
    "bình định": (13.7830, 109.2197),
    "phu yen": (13.0882, 109.0929),
    "phú yên": (13.0882, 109.0929),
    "khanh hoa": (12.2388, 109.1967),
    "khánh hòa": (12.2388, 109.1967),
    "nha trang": (12.2388, 109.1967),
    "ninh thuan": (11.5752, 108.9890),
    "ninh thuận": (11.5752, 108.9890),
    "binh thuan": (10.9282, 108.1021),
    "bình thuận": (10.9282, 108.1021),
    "phan thiet": (10.9282, 108.1021),
    "mui ne": (10.9333, 108.2833),
    "mũi né": (10.9333, 108.2833),
    
    # Tây Nguyên
    "kon tum": (14.3497, 108.0005),
    "gia lai": (13.9833, 108.0),
    "dak lak": (12.6667, 108.05),
    "đắk lắk": (12.6667, 108.05),
    "buon ma thuot": (12.6679, 108.0378),
    "buôn ma thuột": (12.6679, 108.0378),
    "dak nong": (12.0028, 107.6878),
    "đắk nông": (12.0028, 107.6878),
    "lam dong": (11.9404, 108.4583),
    "lâm đồng": (11.9404, 108.4583),
    "da lat": (11.9404, 108.4583),
    "đà lạt": (11.9404, 108.4583),
    "dalat": (11.9404, 108.4583),
    
    # Miền Nam
    "binh phuoc": (11.7512, 106.7235),
    "bình phước": (11.7512, 106.7235),
    "tay ninh": (11.3351, 106.1098),
    "tây ninh": (11.3351, 106.1098),
    "binh duong": (11.0063, 106.6528),
    "bình dương": (11.0063, 106.6528),
    "dong nai": (10.9645, 106.8561),
    "đồng nai": (10.9645, 106.8561),
    "ba ria vung tau": (10.5417, 107.2428),
    "bà rịa vũng tàu": (10.5417, 107.2428),
    "vung tau": (10.3460, 107.0843),
    "vũng tàu": (10.3460, 107.0843),
    "ho chi minh": (10.8231, 106.6297),
    "hồ chí minh": (10.8231, 106.6297),
    "saigon": (10.8231, 106.6297),
    "sài gòn": (10.8231, 106.6297),
    "long an": (10.5440, 106.4053),
    "tiền giang": (10.4493, 106.3420),
    "tien giang": (10.4493, 106.3420),
    "ben tre": (10.2433, 106.3756),
    "bến tre": (10.2433, 106.3756),
    "tra vinh": (9.9347, 106.3455),
    "trà vinh": (9.9347, 106.3455),
    "vinh long": (10.2538, 105.9722),
    "vĩnh long": (10.2538, 105.9722),
    "dong thap": (10.5379, 105.6311),
    "đồng tháp": (10.5379, 105.6311),
    "an giang": (10.3868, 105.4353),
    "can tho": (10.0452, 105.7469),
    "cần thơ": (10.0452, 105.7469),
    "hau giang": (9.7579, 105.6413),
    "hậu giang": (9.7579, 105.6413),
    "soc trang": (9.6038, 105.9800),
    "sóc trăng": (9.6038, 105.9800),
    "bac lieu": (9.2911, 105.7247),
    "bạc liêu": (9.2911, 105.7247),
    "ca mau": (9.1770, 105.1500),
    "cà mau": (9.1770, 105.1500),
    "kien giang": (10.0125, 105.0809),
    "kiên giang": (10.0125, 105.0809),
    "phu quoc": (10.2899, 103.9840),
    "phú quốc": (10.2899, 103.9840),
    
    # Default cho Vietnam
    "vietnam": (16.0583, 108.2772),
    "việt nam": (16.0583, 108.2772),
}

# ────────────────────────────────
# Hàm phân loại khí hậu theo nhiệt độ
# ────────────────────────────────
def climate_label(temp):
    """Phân loại climate dựa trên nhiệt độ"""
    if temp is None:
        return "unknown"
    if temp >= 32:
        return "extremely hot"
    if temp >= 27:
        return "hot"
    if temp >= 23:
        return "warm"
    if temp >= 17:
        return "cool"
    if temp >= 10:
        return "cold"
    return "extremely cold"


# ────────────────────────────────
# Gọi API Open-Meteo
# ────────────────────────────────
def fetch_climate(lat, lon):
    """Gọi Open-Meteo API để lấy nhiệt độ"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        r = requests.get(url, timeout=10)
        d = r.json()
        w = d.get("current_weather", {})
        return w.get("temperature"), w.get("windspeed")
    except Exception as e:
        print(f"Lỗi API: {e}")
        return None, None


# ────────────────────────────────
# Tìm tọa độ từ province
# ────────────────────────────────
def find_coords_for_province(province):
    """Tìm tọa độ dựa trên tên tỉnh"""
    if not province:
        return None, None
    
    province_lower = province.lower().strip()
    
    # Tìm trực tiếp
    if province_lower in PROVINCE_COORDS:
        return PROVINCE_COORDS[province_lower]
    
    # Tìm partial match
    for key, coords in PROVINCE_COORDS.items():
        if key in province_lower or province_lower in key:
            return coords
    
    return None, None


# ────────────────────────────────
# Cập nhật database từ province trong tags
# ────────────────────────────────
def update_database():
    """Cập nhật climate dựa trên province (tags[0])"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lấy danh sách places
    cursor.execute("SELECT id, name, tags FROM place")
    places = cursor.fetchall()
    
    print(f"Tìm thấy {len(places)} địa điểm trong database")
    
    updated = 0
    not_found = 0
    
    # Cache climate theo province để không gọi API nhiều lần
    province_climate_cache = {}
    
    for place_id, name, tags_json in places:
        try:
            tags = json.loads(tags_json) if tags_json else []
        except:
            tags = []
        
        # Lấy province từ tags[0]
        province = tags[0] if tags else None
        
        if not province:
            not_found += 1
            continue
        
        province_lower = province.lower().strip()
        
        # Kiểm tra cache
        if province_lower in province_climate_cache:
            lat, lon, climate = province_climate_cache[province_lower]
        else:
            # Tìm tọa độ
            lat, lon = find_coords_for_province(province)
            
            if lat is None:
                not_found += 1
                continue
            
            # Gọi API lấy climate
            temp, _ = fetch_climate(lat, lon)
            climate = climate_label(temp)
            
            # Lưu cache
            province_climate_cache[province_lower] = (lat, lon, climate)
            
            print(f"  {province}: {climate} ({temp}°C)")
            time.sleep(0.3)  # Rate limiting
        
        # Update database
        cursor.execute("""
            UPDATE place 
            SET lat = ?, lon = ?, climate = ?
            WHERE id = ?
        """, (lat, lon, climate, place_id))
        
        updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n=== KẾT QUẢ ===")
    print(f"Đã cập nhật: {updated} địa điểm")
    print(f"Không tìm thấy province: {not_found} địa điểm")


if __name__ == "__main__":
    print("=== CẬP NHẬT CLIMATE TỪ PROVINCE ===")
    update_database()
