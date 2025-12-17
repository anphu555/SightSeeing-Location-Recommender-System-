"""
Script cập nhật tọa độ chính xác cho các địa điểm du lịch nổi tiếng.
Dữ liệu tọa độ được hardcode cho các địa điểm phổ biến.

Cách chạy:
    cd Backend
    python fix_coordinates.py
"""

import sqlite3
import json

DB_PATH = "vietnamtravel.db"

# ────────────────────────────────
# Tọa độ chính xác cho các địa điểm nổi tiếng
# Format: "tên địa điểm (lowercase)": (lat, lon)
# ────────────────────────────────
FAMOUS_PLACES_COORDS = {
    # Hà Nội
    "temple of literature": (21.0286, 105.8355),
    "temple of literature - imperial academy": (21.0286, 105.8355),
    "ho chi minh mausoleum": (21.0369, 105.8350),
    "hoan kiem lake": (21.0288, 105.8522),
    "west lake": (21.0530, 105.8226),
    "ho tay": (21.0530, 105.8226),
    "ho tay park": (21.0580, 105.8120),
    "one pillar pagoda": (21.0358, 105.8340),
    "hanoi old quarter": (21.0345, 105.8502),
    "thang long imperial citadel": (21.0341, 105.8401),
    "tran quoc pagoda": (21.0480, 105.8365),
    
    # Hồ Chí Minh
    "cu chi tunnels": (11.1429, 106.4622),
    "independence palace": (10.7769, 106.6953),
    "reunification palace": (10.7769, 106.6953),
    "notre dame cathedral": (10.7798, 106.6990),
    "saigon notre dame cathedral": (10.7798, 106.6990),
    "ben thanh market": (10.7725, 106.6980),
    "war remnants museum": (10.7794, 106.6920),
    "giac lam pagoda": (10.7880, 106.6340),
    "suoi tien tourist area": (10.8700, 106.7750),
    "suoi tien": (10.8700, 106.7750),
    "vinh nghiem pagoda": (10.7924, 106.6838),
    "bitexco financial tower": (10.7716, 106.7042),
    "saigon river": (10.7867, 106.7100),
    "dam sen park": (10.7681, 106.6328),
    "binh quoi tourist village": (10.8390, 106.7270),
    
    # Đà Nẵng
    "my khe beach": (16.0544, 108.2422),
    "marble mountains": (16.0044, 108.2628),
    "ngu hanh son": (16.0044, 108.2628),
    "dragon bridge": (16.0610, 108.2278),
    "ba na hills": (15.9977, 107.9878),
    "son tra peninsula": (16.1184, 108.2722),
    "han river bridge": (16.0611, 108.2252),
    "linh ung pagoda": (16.1003, 108.2775),
    "lady buddha": (16.1003, 108.2775),
    "nam o beach": (16.1050, 108.1260),
    
    # Huế
    "hue imperial city": (16.4698, 107.5779),
    "imperial city of hue": (16.4698, 107.5779),
    "thien mu pagoda": (16.4536, 107.5482),
    "khai dinh tomb": (16.4056, 107.5959),
    "minh mang tomb": (16.4077, 107.5382),
    "tu duc tomb": (16.4340, 107.5468),
    "hue citadel": (16.4698, 107.5779),
    "perfume river": (16.4550, 107.5700),
    
    # Hội An
    "hoi an ancient town": (15.8801, 108.3380),
    "japanese covered bridge": (15.8773, 108.3270),
    "an bang beach": (15.8993, 108.3614),
    "cua dai beach": (15.8802, 108.3691),
    "tra que vegetable village": (15.8900, 108.3510),
    
    # Quảng Ninh / Hạ Long
    "ha long bay": (20.9101, 107.1839),
    "halong bay": (20.9101, 107.1839),
    "bai chay beach": (20.9550, 107.0700),
    "tuan chau island": (20.9340, 107.0330),
    "sung sot cave": (20.8380, 107.1130),
    "ti top island": (20.8230, 107.0520),
    "cat ba island": (20.7256, 107.0457),
    
    # Ninh Bình
    "trang an landscape complex": (20.2419, 105.9383),
    "trang an": (20.2419, 105.9383),
    "bai dinh pagoda": (20.2708, 105.8861),
    "tam coc": (20.2154, 105.9294),
    "tam coc - bich dong": (20.2154, 105.9294),
    "mua cave": (20.2083, 105.9206),
    "hang mua": (20.2083, 105.9206),
    
    # Lào Cai / Sapa
    "sapa": (22.3364, 103.8438),
    "sa pa": (22.3364, 103.8438),
    "fansipan": (22.3033, 103.7750),
    "cat cat village": (22.3280, 103.8280),
    "ham rong mountain": (22.3380, 103.8400),
    "muong hoa valley": (22.2833, 103.8667),
    
    # Nha Trang
    "nha trang beach": (12.2388, 109.1967),
    "vinpearl land nha trang": (12.2118, 109.2356),
    "po nagar cham towers": (12.2650, 109.1961),
    "hon chong promontory": (12.2683, 109.2000),
    "long son pagoda": (12.2510, 109.1780),
    
    # Đà Lạt
    "xuan huong lake": (11.9420, 108.4413),
    "datanla waterfall": (11.8970, 108.4500),
    "prenn waterfall": (11.8560, 108.4320),
    "dalat flower garden": (11.9480, 108.4410),
    "crazy house": (11.9342, 108.4307),
    "dalat railway station": (11.9363, 108.4494),
    "lang biang mountain": (12.0500, 108.4380),
    
    # Phú Quốc
    "phu quoc island": (10.2899, 103.9840),
    "sao beach": (10.1400, 104.0150),
    "bai sao": (10.1400, 104.0150),
    "vinpearl safari phu quoc": (10.3280, 103.8680),
    "dinh cau temple": (10.2133, 103.9600),
    "phu quoc prison": (10.3367, 104.0017),
    
    # Vũng Tàu
    "vung tau beach": (10.3460, 107.0843),
    "front beach": (10.3417, 107.0756),
    "back beach": (10.3280, 107.0880),
    "christ of vung tau": (10.3278, 107.0892),
    "ho may park": (10.3120, 107.0830),
    
    # Cần Thơ
    "cai rang floating market": (10.0167, 105.7667),
    "ninh kieu wharf": (10.0330, 105.7850),
    
    # Quảng Bình
    "phong nha cave": (17.5905, 106.2830),
    "phong nha ke bang": (17.5905, 106.2830),
    "paradise cave": (17.5600, 106.2100),
    "son doong cave": (17.4500, 106.2860),
    
    # An Giang
    "tra su melaleuca forest": (10.5180, 105.0980),
    "tra su": (10.5180, 105.0980),
    "ba chua xu temple": (10.6892, 105.1419),
    "sam mountain": (10.6750, 105.1400),
    "cam mountain": (10.5300, 105.0100),
    
    # Bình Thuận / Mũi Né
    "mui ne sand dunes": (10.9333, 108.2833),
    "white sand dunes": (11.0083, 108.4250),
    "red sand dunes": (10.9333, 108.2833),
    "fairy stream": (10.9333, 108.2833),
    
    # Bắc Giang
    "tho ha communal house": (21.2860, 106.2030),
}

# ────────────────────────────────
# Tọa độ trung tâm các tỉnh (fallback cho các địa điểm không có trong danh sách trên)
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
    "thua thien hue": (16.4674, 107.5905),
    "thừa thiên huế": (16.4674, 107.5905),
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
    "dalat": (11.9404, 108.4583),
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
    "bac ninh": (21.1214, 106.1111),
    "bắc ninh": (21.1214, 106.1111),
    "dong nai": (10.9645, 106.8561),
    "đồng nai": (10.9645, 106.8561),
    "binh duong": (11.0063, 106.6528),
    "bình dương": (11.0063, 106.6528),
    "tay ninh": (11.3351, 106.1098),
    "tây ninh": (11.3351, 106.1098),
    "ben tre": (10.2433, 106.3756),
    "bến tre": (10.2433, 106.3756),
    "tra vinh": (9.9347, 106.3455),
    "trà vinh": (9.9347, 106.3455),
    "soc trang": (9.6038, 105.9800),
    "sóc trăng": (9.6038, 105.9800),
    "ca mau": (9.1770, 105.1500),
    "cà mau": (9.1770, 105.1500),
    "long an": (10.5440, 106.4053),
    "tien giang": (10.4493, 106.3420),
    "tiền giang": (10.4493, 106.3420),
    "vinh long": (10.2538, 105.9722),
    "vĩnh long": (10.2538, 105.9722),
    "dong thap": (10.5379, 105.6311),
    "đồng tháp": (10.5379, 105.6311),
    "ha giang": (22.8233, 104.9838),
    "hà giang": (22.8233, 104.9838),
    "cao bang": (22.6666, 106.2580),
    "cao bằng": (22.6666, 106.2580),
    "lang son": (21.8537, 106.7613),
    "lạng sơn": (21.8537, 106.7613),
    "son la": (21.3269, 103.9144),
    "sơn la": (21.3269, 103.9144),
    "dien bien": (21.3867, 103.0230),
    "điện biên": (21.3867, 103.0230),
    "lai chau": (22.3860, 103.4594),
    "lai châu": (22.3860, 103.4594),
    "yen bai": (21.7236, 104.9113),
    "yên bái": (21.7236, 104.9113),
    "phu tho": (21.3229, 105.2016),
    "phú thọ": (21.3229, 105.2016),
    "thai nguyen": (21.5928, 105.8442),
    "thái nguyên": (21.5928, 105.8442),
    "bac kan": (22.1471, 105.8347),
    "bắc kạn": (22.1471, 105.8347),
    "tuyen quang": (21.8230, 105.2140),
    "tuyên quang": (21.8230, 105.2140),
    "vinh phuc": (21.3609, 105.5474),
    "vĩnh phúc": (21.3609, 105.5474),
    "ha nam": (20.5835, 105.9230),
    "hà nam": (20.5835, 105.9230),
    "nam dinh": (20.4200, 106.1683),
    "nam định": (20.4200, 106.1683),
    "thai binh": (20.4463, 106.3422),
    "thái bình": (20.4463, 106.3422),
    "hung yen": (20.6464, 106.0511),
    "hưng yên": (20.6464, 106.0511),
    "hai duong": (20.9374, 106.3146),
    "hải dương": (20.9374, 106.3146),
    "hoa binh": (20.8169, 105.3381),
    "hòa bình": (20.8169, 105.3381),
    "quang tri": (16.7579, 107.1856),
    "quảng trị": (16.7579, 107.1856),
    "ha tinh": (18.3559, 105.8877),
    "hà tĩnh": (18.3559, 105.8877),
    "quang ngai": (15.1205, 108.8042),
    "quảng ngãi": (15.1205, 108.8042),
    "binh dinh": (13.7830, 109.2197),
    "bình định": (13.7830, 109.2197),
    "phu yen": (13.0882, 109.0929),
    "phú yên": (13.0882, 109.0929),
    "ninh thuan": (11.5752, 108.9890),
    "ninh thuận": (11.5752, 108.9890),
    "kon tum": (14.3497, 108.0005),
    "gia lai": (13.9833, 108.0),
    "dak lak": (12.6667, 108.05),
    "đắk lắk": (12.6667, 108.05),
    "buon ma thuot": (12.6679, 108.0378),
    "buôn ma thuột": (12.6679, 108.0378),
    "dak nong": (12.0028, 107.6878),
    "đắk nông": (12.0028, 107.6878),
    "binh phuoc": (11.7512, 106.7235),
    "bình phước": (11.7512, 106.7235),
    "bac lieu": (9.2911, 105.7247),
    "bạc liêu": (9.2911, 105.7247),
    "hau giang": (9.7579, 105.6413),
    "hậu giang": (9.7579, 105.6413),
}


def find_coords(place_name, province=None):
    """
    Tìm tọa độ cho một địa điểm.
    1. Tìm trong danh sách địa điểm nổi tiếng
    2. Fallback về tọa độ tỉnh
    """
    name_lower = place_name.lower().strip()
    
    # 1. Tìm exact match trong famous places
    if name_lower in FAMOUS_PLACES_COORDS:
        return FAMOUS_PLACES_COORDS[name_lower]
    
    # 2. Tìm partial match trong famous places
    for key, coords in FAMOUS_PLACES_COORDS.items():
        if key in name_lower or name_lower in key:
            return coords
    
    # 3. Fallback về tọa độ tỉnh
    if province:
        province_lower = province.lower().strip()
        if province_lower in PROVINCE_COORDS:
            return PROVINCE_COORDS[province_lower]
        
        # Partial match cho province
        for key, coords in PROVINCE_COORDS.items():
            if key in province_lower or province_lower in key:
                return coords
    
    return None, None


def update_all_coordinates():
    """Cập nhật tọa độ cho tất cả địa điểm trong database"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, tags FROM place")
    places = cursor.fetchall()
    
    print(f"Đang cập nhật {len(places)} địa điểm...")
    print("="*60)
    
    famous_match = 0
    province_match = 0
    no_match = 0
    
    for place_id, name, tags_json in places:
        try:
            tags = json.loads(tags_json) if tags_json else []
        except:
            tags = []
        
        province = tags[0] if tags else None
        name_lower = name.lower().strip()
        
        # Tìm tọa độ
        lat, lon = None, None
        
        # 1. Exact match famous places
        if name_lower in FAMOUS_PLACES_COORDS:
            lat, lon = FAMOUS_PLACES_COORDS[name_lower]
            famous_match += 1
        else:
            # 2. Partial match famous places
            found = False
            for key, coords in FAMOUS_PLACES_COORDS.items():
                if key in name_lower or name_lower in key:
                    lat, lon = coords
                    famous_match += 1
                    found = True
                    break
            
            # 3. Fallback về tọa độ tỉnh
            if not found and province:
                province_lower = province.lower().strip()
                if province_lower in PROVINCE_COORDS:
                    lat, lon = PROVINCE_COORDS[province_lower]
                    province_match += 1
                else:
                    for key, coords in PROVINCE_COORDS.items():
                        if key in province_lower or province_lower in key:
                            lat, lon = coords
                            province_match += 1
                            break
                    else:
                        no_match += 1
            elif not found:
                no_match += 1
        
        # Update database
        if lat is not None:
            cursor.execute("UPDATE place SET lat = ?, lon = ? WHERE id = ?", (lat, lon, place_id))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Famous places match: {famous_match}")
    print(f"✓ Province fallback: {province_match}")
    print(f"✗ No match: {no_match}")
    print("="*60)
    print("Hoàn thành!")


if __name__ == "__main__":
    print("=== CẬP NHẬT TỌA ĐỘ CHO CÁC ĐỊA ĐIỂM ===")
    update_all_coordinates()
