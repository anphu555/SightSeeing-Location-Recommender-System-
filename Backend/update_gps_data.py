"""
Script để cập nhật tọa độ GPS cho các địa điểm trong database
Chạy file này để thêm dữ liệu GPS mẫu
"""
import sqlite3
import os

# GPS data cho các địa điểm nổi tiếng ở Việt Nam
SAMPLE_GPS_DATA = {
    # Hà Nội
    "Hồ Hoàn Kiếm": (21.0285, 105.8542),
    "Văn Miếu Quốc Tử Giám": (21.0277, 105.8355),
    "Lăng Chủ tịch Hồ Chí Minh": (21.0369, 105.8345),
    "Chùa Một Cột": (21.0361, 105.8341),
    "Phố cổ Hà Nội": (21.0352, 105.8516),
    "Hồ Tây": (21.0583, 105.8189),
    
    # Hạ Long - Quảng Ninh
    "Vịnh Hạ Long": (20.9101, 107.1839),
    "Đảo Cát Bà": (20.7273, 107.0479),
    
    # Đà Nẵng
    "Cầu Rồng": (16.0611, 108.2277),
    "Bà Nà Hills": (15.9953, 107.9944),
    "Bãi biển Mỹ Khê": (16.0477, 108.2394),
    "Ngũ Hành Sơn": (16.0034, 108.2636),
    "Bán đảo Sơn Trà": (16.1075, 108.2704),
    
    # Hội An
    "Phố cổ Hội An": (15.8801, 108.3380),
    "Cầu Nhật Bản": (15.8794, 108.3269),
    
    # Huế
    "Đại Nội Huế": (16.4673, 107.5801),
    "Lăng Khải Định": (16.4468, 107.6443),
    "Chùa Thiên Mụ": (16.4518, 107.5454),
    
    # TP.HCM (Sài Gòn)
    "Nhà thờ Đức Bà": (10.7797, 106.6990),
    "Dinh Độc Lập": (10.7770, 106.6952),
    "Chợ Bến Thành": (10.7723, 106.6980),
    "Bitexco Financial Tower": (10.7717, 106.7043),
    
    # Nha Trang
    "Bãi biển Nha Trang": (12.2451, 109.1943),
    "Vinpearl Land": (12.2163, 109.2432),
    "Tháp Bà Ponagar": (12.2649, 109.1953),
    
    # Phú Quốc
    "Bãi Sao": (10.1610, 103.9695),
    "Dinh Cậu": (10.2258, 103.9673),
    
    # Đà Lạt
    "Hồ Xuân Hương": (11.9404, 108.4383),
    "Thác Datanla": (11.9125, 108.4372),
    "Ga Đà Lạt": (11.9436, 108.4422),
    
    # Mũi Né - Phan Thiết
    "Đồi cát bay": (10.9506, 108.2856),
    "Suối Tiên": (11.0141, 108.2627),
    
    # Sapa
    "Núi Hàm Rồng": (22.3405, 103.8445),
    "Thác Bạc": (22.3649, 103.8267),
    
    # Ninh Bình
    "Tràng An": (20.2514, 105.9145),
    "Tam Cốc": (20.2447, 105.9177),
    "Bái Đính": (20.2178, 105.8933),
    
    # Vũng Tàu
    "Tượng Chúa Kitô": (10.3294, 107.0741),
    "Bãi Sau": (10.3382, 107.0936),
}

def get_db_path():
    """Lấy đường dẫn đến database"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "vietnamtravel.db")

def update_place_gps(place_name: str, latitude: float, longitude: float):
    """Cập nhật GPS cho một địa điểm cụ thể"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Tìm place theo tên (partial match)
        cursor.execute(
            "SELECT id, name FROM place WHERE name LIKE ?",
            (f"%{place_name}%",)
        )
        results = cursor.fetchall()
        
        if results:
            for place_id, full_name in results:
                cursor.execute(
                    "UPDATE place SET latitude = ?, longitude = ? WHERE id = ?",
                    (latitude, longitude, place_id)
                )
                print(f"✅ Updated: {full_name} -> ({latitude}, {longitude})")
            conn.commit()
            return True
        else:
            print(f"⚠️  Not found: {place_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {place_name}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def bulk_update_gps():
    """Cập nhật hàng loạt các địa điểm"""
    print("🚀 Starting GPS data update...")
    print(f"📊 Total places to update: {len(SAMPLE_GPS_DATA)}\n")
    
    success_count = 0
    fail_count = 0
    
    for place_name, (lat, lon) in SAMPLE_GPS_DATA.items():
        if update_place_gps(place_name, lat, lon):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Success: {success_count} places")
    print(f"❌ Failed: {fail_count} places")
    print(f"{'='*50}")

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
    
    print(f"\n📍 GPS Statistics:")
    print(f"   Total places: {total}")
    print(f"   Places with GPS: {with_gps}")
    print(f"   Coverage: {(with_gps/total*100):.1f}%")

if __name__ == "__main__":
    print("=" * 50)
    print("  GPS DATA UPDATER FOR VIETNAM TRAVEL DATABASE")
    print("=" * 50)
    
    # Show before stats
    show_stats()
    
    # Update GPS data
    bulk_update_gps()
    
    # Show after stats
    show_stats()
    
    print("\n✨ Done! You can now use the 'Near Me' sort feature.\n")
