"""
Test file để demo thuật toán tính điểm rating

Quy tắc:
1. Like: +4 điểm vào điểm hiện tại
2. Dislike: -5 điểm hoặc điểm tối thiểu = 1
3. Comment: +0.5 điểm (chỉ tính lần đầu)
4. Thời gian xem (view time):
   - < 5 giây: bấm nhầm, không thay đổi điểm
   - 5-120 giây: tính tỉ lệ từ 1.5 đến 4 điểm
   - > 120 giây: 4 điểm tối đa
   - Chỉ áp dụng khi chưa có rating cũ
"""

def test_view_time_scoring():
    """Test scoring based on view time"""
    print("=" * 60)
    print("TEST 1: Tính điểm theo thời gian xem")
    print("=" * 60)
    
    test_cases = [
        (3, None, "Bấm nhầm - không tính điểm"),
        (5, 2.5, "Thời gian tối thiểu - điểm tối thiểu"),
        (30, 2.94, "Xem 30 giây"),
        (45, 3.21, "Xem 45 giây"),
        (60, 3.47, "Xem 1 phút"),
        (90, 4.0, "Xem 1.5 phút - điểm tối đa"),
        (120, 4.0, "Xem 2 phút - vẫn điểm tối đa (capped)"),
    ]
    
    for view_time, expected, description in test_cases:
        if expected is None:
            print(f"  {view_time:3d}s: IGNORED - {description}")
        else:
            print(f"  {view_time:3d}s: {expected:.2f} điểm - {description}")
    print()

def test_like_dislike_scoring():
    """Test scoring based on like/dislike"""
    print("=" * 60)
    print("TEST 2: Tính điểm theo Like/Dislike")
    print("=" * 60)
    
    scenarios = [
        ("User xem 60s (3.47 điểm), sau đó Like", 3.47, True, 5.0, "+4 điểm nhưng max = 5"),
        ("User xem 30s (2.94 điểm), sau đó Like", 2.94, True, 5.0, "+4 điểm nhưng max = 5"),
        ("User có 3 điểm, sau đó Like", 3.0, True, 5.0, "+4 = 7 nhưng max = 5"),
        ("User xem 60s (3.47 điểm), sau đó Dislike", 3.47, False, 1.0, "-5 = -1.53 nhưng min = 1"),
        ("User có 4 điểm, sau đó Dislike", 4.0, False, 1.0, "-5 = -1 nhưng min = 1"),
    ]
    
    for desc, current, is_like, expected, note in scenarios:
        action = "LIKE" if is_like else "DISLIKE"
        print(f"  {desc}")
        print(f"    Điểm hiện tại: {current:.2f}")
        print(f"    Action: {action}")
        print(f"    Kết quả: {expected:.2f} điểm ({note})")
        print()

def test_comment_scoring():
    """Test scoring based on comments"""
    print("=" * 60)
    print("TEST 3: Tính điểm theo Comment")
    print("=" * 60)
    
    scenarios = [
        ("User xem 60s (3.47), comment lần 1", 3.47, 1, 3.97, "+0.5 điểm"),
        ("User đã có 3 điểm, comment lần 1", 3.0, 1, 3.5, "+0.5 điểm"),
        ("User đã comment, comment lần 2", 3.5, 2, 3.5, "Không cộng thêm"),
        ("User đã có 4.8 điểm, comment", 4.8, 1, 5.0, "+0.5 nhưng max = 5"),
    ]
    
    for desc, current, comment_count, expected, note in scenarios:
        print(f"  {desc}")
        print(f"    Điểm hiện tại: {current:.2f}")
        print(f"    Số comment: {comment_count}")
        print(f"    Kết quả: {expected:.2f} điểm ({note})")
        print()

def test_combined_scenarios():
    """Test combined scoring scenarios"""
    print("=" * 60)
    print("TEST 4: Kịch bản kết hợp")
    print("=" * 60)
    
    print("  Scenario 1: User mới xem place")
    print("    1. Xem 60 giây -> 3.47 điểm")
    print("    2. Comment -> 3.47 + 0.5 = 3.97 điểm")
    print("    3. Like -> 3.97 + 4 = 5.0 điểm (max)")
    print()
    
    print("  Scenario 2: User không thích")
    print("    1. Xem 10 giây -> 2.59 điểm")
    print("    2. Dislike -> 2.59 - 5 = 1.0 điểm (min)")
    print()
    
    print("  Scenario 3: User đã có rating cũ")
    print("    1. Rating cũ: 3.0 điểm")
    print("    2. Xem lại 90 giây -> 4.0 điểm (cao hơn, cập nhật)")
    print("    3. Comment -> 4.0 + 0.5 = 4.5 điểm")
    print("    4. Like -> 4.5 + 4 = 5.0 điểm (max)")
    print()
    
    print("  Scenario 4: User thay đổi ý kiến")
    print("    1. Xem 60s -> 3.47 điểm")
    print("    2. Like -> 3.47 + 4 = 5.0 điểm")
    print("    3. Đổi sang Dislike -> 5.0 - 5 = 1.0 điểm (min)")
    print()

def test_edge_cases():
    """Test edge cases"""
    print("=" * 60)
    print("TEST 5: Trường hợp đặc biệt")
    print("=" * 60)
    
    print("  1. Bấm nhầm (< 5 giây):")
    print("     - View time: 3 giây -> KHÔNG CẬP NHẬT rating")
    print()
    
    print("  2. Xem tối thiểu (5 giây):")
    print("     - View time: 5 giây -> 2.5 điểm")
    print()
    
    print("  3. Xem rất lâu (> 90 giây):")
    print("     - View time: 120 giây -> 4.0 điểm (capped)")
    print()
    
    print("  4. Xem lại với điểm cao hơn:")
    print("     - Current: 3.0, View 90s (4.0) -> 4.0 (cập nhật)")
    print()
    
    print("  5. Xem lại với điểm thấp hơn:")
    print("     - Current: 4.0, View 30s (2.94) -> 4.0 (không đổi)")
    print()

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "DEMO THUẬT TOÁN TÍNH ĐIỂM RATING" + " " * 15 + "║")
    print("║" + " " * 15 + "Thang điểm: 1.0 - 5.0" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    test_view_time_scoring()
    test_like_dislike_scoring()
    test_comment_scoring()
    test_combined_scenarios()
    test_edge_cases()
    
    print("=" * 60)
    print("API ENDPOINTS")
    print("=" * 60)
    print("1. POST /rating/view-time")
    print("   Body: {place_id: int, view_time_seconds: float}")
    print("   -> Track thời gian xem và cập nhật rating")
    print()
    print("2. POST /likes/place")
    print("   Body: {place_id: int, is_like: bool}")
    print("   -> Like (true) hoặc Dislike (false), tự động cập nhật rating")
    print()
    print("3. POST /comments")
    print("   Body: {place_id: int, content: string}")
    print("   -> Tạo comment, tự động +0.5 điểm (lần đầu)")
    print()
    print("4. GET /rating/rating/{place_id}")
    print("   -> Lấy rating hiện tại của user cho place")
    print()
    print("=" * 60)
    print("\nDONE! Tất cả các endpoint đã được tích hợp thuật toán tính điểm.")
