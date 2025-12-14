"""
Script để cập nhật GPS cho TẤT CẢ địa điểm dựa trên province/tags
Sử dụng tọa độ trung tâm của từng tỉnh/thành phố
"""
import sqlite3
import os
import json
import random

# Tọa độ trung tâm của các tỉnh/thành phố Việt Nam
PROVINCE_GPS = {
    # Miền Bắc
    "Hà Nội": (21.0285, 105.8542),
    "Hanoi": (21.0285, 105.8542),
    "Quảng Ninh": (20.9511, 107.0864),
    "Quang Ninh": (20.9511, 107.0864),
    "Hải Phòng": (20.8449, 106.6881),
    "Hai Phong": (20.8449, 106.6881),
    "Ninh Bình": (20.2506, 105.9745),
    "Ninh Binh": (20.2506, 105.9745),
    "Lào Cai": (22.4809, 103.9755),
    "Lao Cai": (22.4809, 103.9755),
    "Điện Biên": (21.3836, 103.0171),
    "Dien Bien": (21.3836, 103.0171),
    "Hòa Bình": (20.6861, 105.3131),
    "Hoa Binh": (20.6861, 105.3131),
    "Thái Nguyên": (21.5671, 105.8252),
    "Thai Nguyen": (21.5671, 105.8252),
    "Bắc Giang": (21.2819, 106.1975),
    "Bac Giang": (21.2819, 106.1975),
    "Bắc Kạn": (22.1474, 105.8348),
    "Bac Kan": (22.1474, 105.8348),
    "Cao Bằng": (22.6666, 106.2523),
    "Cao Bang": (22.6666, 106.2523),
    
    # Miền Trung
    "Đà Nẵng": (16.0544, 108.2022),
    "Da Nang": (16.0544, 108.2022),
    "Huế": (16.4637, 107.5909),
    "Hue": (16.4637, 107.5909),
    "Thừa Thiên Huế": (16.4637, 107.5909),
    "Thua Thien Hue": (16.4637, 107.5909),
    "Quảng Nam": (15.5394, 108.0191),
    "Quang Nam": (15.5394, 108.0191),
    "Quảng Ngãi": (15.1214, 108.8044),
    "Quang Ngai": (15.1214, 108.8044),
    "Bình Định": (13.7829, 109.2196),
    "Binh Dinh": (13.7829, 109.2196),
    "Phú Yên": (13.0882, 109.0929),
    "Phu Yen": (13.0882, 109.0929),
    "Khánh Hòa": (12.2585, 109.0526),
    "Khanh Hoa": (12.2585, 109.0526),
    "Nha Trang": (12.2388, 109.1967),
    "Ninh Thuận": (11.6739, 108.8629),
    "Ninh Thuan": (11.6739, 108.8629),
    "Bình Thuận": (10.9273, 108.1015),
    "Binh Thuan": (10.9273, 108.1015),
    "Phan Thiết": (10.9276, 108.1010),
    "Phan Thiet": (10.9276, 108.1010),
    "Kon Tum": (14.3497, 108.0005),
    "Gia Lai": (13.9833, 108.0000),
    "Đắk Lắk": (12.7100, 108.2378),
    "Dak Lak": (12.7100, 108.2378),
    "Đắk Nông": (12.0046, 107.6097),
    "Dak Nong": (12.0046, 107.6097),
    "Lâm Đồng": (11.5753, 108.1429),
    "Lam Dong": (11.5753, 108.1429),
    "Đà Lạt": (11.9404, 108.4583),
    "Da Lat": (11.9404, 108.4583),
    
    # Miền Nam
    "TP.HCM": (10.7769, 106.7009),
    "Hồ Chí Minh": (10.7769, 106.7009),
    "Ho Chi Minh": (10.7769, 106.7009),
    "Ho Chi Minh City": (10.7769, 106.7009),
    "Sài Gòn": (10.7769, 106.7009),
    "Saigon": (10.7769, 106.7009),
    "Vũng Tàu": (10.3458, 107.0843),
    "Vung Tau": (10.3458, 107.0843),
    "Bà Rịa - Vũng Tàu": (10.5417, 107.2430),
    "Ba Ria - Vung Tau": (10.5417, 107.2430),
    "Đồng Nai": (10.9519, 106.8383),
    "Dong Nai": (10.9519, 106.8383),
    "Bình Dương": (11.3254, 106.4770),
    "Binh Duong": (11.3254, 106.4770),
    "Long An": (10.5355, 106.4056),
    "Tiền Giang": (10.3599, 106.3621),
    "Tien Giang": (10.3599, 106.3621),
    "Bến Tre": (10.2433, 106.3757),
    "Ben Tre": (10.2433, 106.3757),
    "Vĩnh Long": (10.2397, 105.9722),
    "Vinh Long": (10.2397, 105.9722),
    "Trà Vinh": (9.8124, 106.2992),
    "Tra Vinh": (9.8124, 106.2992),
    "Cần Thơ": (10.0452, 105.7469),
    "Can Tho": (10.0452, 105.7469),
    "An Giang": (10.5215, 105.1258),
    "Kiên Giang": (10.0125, 105.0808),
    "Kien Giang": (10.0125, 105.0808),
    "Phú Quốc": (10.2898, 103.9850),
    "Phu Quoc": (10.2898, 103.9850),
    "Cà Mau": (9.1526, 105.1960),
    "Ca Mau": (9.1526, 105.1960),
    "Bạc Liêu": (9.2515, 105.7244),
    "Bac Lieu": (9.2515, 105.7244),
    "Sóc Trăng": (9.6037, 105.9739),
    "Soc Trang": (9.6037, 105.9739),
    "Hậu Giang": (9.7577, 105.6412),
    "Hau Giang": (9.7577, 105.6412),
}

def get_db_path():
    """Lấy đường dẫn đến database"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "vietnamtravel.db")

def add_small_random_offset(lat, lon):
    """Thêm offset ngẫu nhiên nhỏ để các địa điểm trong cùng tỉnh không trùng GPS hoàn toàn"""
    # Offset trong khoảng ±0.1 độ (~ ±11km)
    lat_offset = random.uniform(-0.1, 0.1)
    lon_offset = random.uniform(-0.1, 0.1)
    return (round(lat + lat_offset, 6), round(lon + lon_offset, 6))

def update_all_places_gps():
    """Cập nhật GPS cho TẤT CẢ địa điểm dựa trên tags (province)"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Starting bulk GPS update for all places...\n")
    
    # Lấy tất cả places
    cursor.execute("SELECT id, name, tags FROM place")
    all_places = cursor.fetchall()
    
    updated = 0
    skipped = 0
    
    for place_id, name, tags_json in all_places:
        try:
            # Parse tags (JSON array)
            tags = json.loads(tags_json) if tags_json else []
            
            # Lấy province (thường là tag đầu tiên)
            province = tags[0] if tags and len(tags) > 0 else None
            
            if not province:
                print(f"⚠️  {name}: No province tag found")
                skipped += 1
                continue
            
            # Tìm GPS của province
            base_gps = PROVINCE_GPS.get(province)
            
            if base_gps:
                # Thêm offset nhỏ để không trùng hoàn toàn
                lat, lon = add_small_random_offset(base_gps[0], base_gps[1])
                
                cursor.execute(
                    "UPDATE place SET latitude = ?, longitude = ? WHERE id = ?",
                    (lat, lon, place_id)
                )
                
                print(f"✅ {name} ({province}) -> ({lat}, {lon})")
                updated += 1
            else:
                print(f"⚠️  {name}: Province '{province}' not in GPS database")
                skipped += 1
                
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")
            skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Updated: {updated} places")
    print(f"⚠️  Skipped: {skipped} places")
    print(f"{'='*60}")
    
    return updated, skipped

def show_stats():
    """Hiển thị thống kê places có GPS"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM place")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM place WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    with_gps = cursor.fetchone()[0]
    
    conn.close()
    
    percentage = (with_gps/total*100) if total > 0 else 0
    
    print(f"\n📍 GPS Coverage Statistics:")
    print(f"   Total places in database: {total}")
    print(f"   Places with GPS data: {with_gps}")
    print(f"   Coverage: {percentage:.1f}%")
    
    if percentage < 100:
        print(f"   ⚠️  {total - with_gps} places still missing GPS data")

if __name__ == "__main__":
    print("=" * 60)
    print("     GPS BULK UPDATER FOR VIETNAM TRAVEL DATABASE")
    print("=" * 60)
    
    # Show before stats
    print("\n📊 BEFORE UPDATE:")
    show_stats()
    
    # Confirm before proceeding
    print("\n⚠️  This will update GPS coordinates for ALL places in the database.")
    response = input("   Do you want to continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        # Update GPS data
        updated, skipped = update_all_places_gps()
        
        # Show after stats
        print("\n📊 AFTER UPDATE:")
        show_stats()
        
        print("\n✨ Done! You can now use the 'Near Me' sort feature on the website.")
        print("   Note: GPS coordinates are based on province centers with small random offsets.\n")
    else:
        print("\n❌ Operation cancelled by user.\n")
