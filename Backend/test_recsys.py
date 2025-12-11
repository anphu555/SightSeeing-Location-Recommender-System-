"""
Test script for Content-Based Recommendation System
Kiểm tra xem model có hoạt động đúng không
"""

import sys
sys.path.append('/home/shiki/SightSeeing-Location-Recommender-System-/Backend')

from app.routers.recsysmodel import recommend_two_tower, initialize_recsys

def test_recommendation():
    """Test basic recommendation functionality"""
    
    print("=" * 60)
    print("TESTING CONTENT-BASED RECOMMENDATION SYSTEM")
    print("=" * 60)
    
    # Initialize system
    print("\n1. Khởi tạo hệ thống...")
    initialize_recsys()
    print("✅ Khởi tạo thành công!")
    
    # Test cases
    test_cases = [
        {
            "name": "Beach lover",
            "tags": ["Beach", "Coastal", "Sea"],
            "description": "User thích biển và các hoạt động ven biển"
        },
        {
            "name": "History enthusiast",
            "tags": ["Historical", "Temple", "Cultural Heritage"],
            "description": "User thích lịch sử và văn hóa"
        },
        {
            "name": "Nature explorer",
            "tags": ["Nature", "Mountain", "Cave"],
            "description": "User thích khám phá thiên nhiên"
        },
        {
            "name": "Hanoi visitor",
            "tags": ["Hanoi", "City", "Food"],
            "description": "User muốn tham quan Hà Nội"
        }
    ]
    
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST CASE {idx}: {test_case['name']}")
        print(f"Mô tả: {test_case['description']}")
        print(f"Tags: {test_case['tags']}")
        print(f"{'-' * 60}")
        
        try:
            results = recommend_two_tower(test_case['tags'], top_k=5)
            
            if results.empty:
                print("⚠️ Không có kết quả nào được trả về!")
            else:
                print(f"✅ Tìm thấy {len(results)} địa điểm:\n")
                for i, (_, row) in enumerate(results.iterrows(), 1):
                    print(f"   {i}. [{row['province']}] {row['name']}")
                    print(f"      Score: {row['score']:.4f}")
                    print(f"      Tags: {row['tags'][:3]}...")  # Show first 3 tags
                    print()
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")
    
    print("=" * 60)
    print("TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_recommendation()
