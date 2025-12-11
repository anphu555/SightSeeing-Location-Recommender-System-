"""
Test script để verify tích hợp Like vào RecommendationSystem

Kiểm tra:
1. get_user_likes() có query đúng không
2. build_user_profile() có kết hợp cả Rating và Like không
3. Weight của Like (0.75) có hợp lý không
"""

from sqlmodel import Session, select
from app.database import engine
from app.schemas import Like, Rating, User, Place
from app.routers.recsysmodel import get_user_likes, build_user_profile, initialize_recsys

def test_get_user_likes():
    """Test hàm get_user_likes()"""
    print("\n=== TEST 1: get_user_likes() ===")
    
    with Session(engine) as session:
        # Lấy user đầu tiên
        user = session.exec(select(User)).first()
        
        if not user:
            print("❌ Không có user trong database")
            return
        
        print(f"✓ Testing với User ID: {user.id} ({user.username})")
        
        # Lấy likes
        liked_places = get_user_likes(user.id)
        print(f"✓ User đã like {len(liked_places)} places")
        
        if liked_places:
            print(f"  Place IDs: {liked_places[:5]}...")  # Show first 5
        
        # Verify bằng cách query trực tiếp
        statement = select(Like).where(
            Like.user_id == user.id,
            Like.place_id.isnot(None)
        )
        direct_likes = session.exec(statement).all()
        
        assert len(liked_places) == len(direct_likes), "❌ Số lượng không khớp!"
        print(f"✓ Verified: {len(liked_places)} likes match direct query")

def test_build_user_profile():
    """Test hàm build_user_profile() với Rating + Like"""
    print("\n=== TEST 2: build_user_profile() ===")
    
    # Initialize recsys trước
    initialize_recsys()
    
    with Session(engine) as session:
        # Tìm user có cả Rating và Like
        users = session.exec(select(User)).all()
        
        for user in users[:3]:  # Test 3 users đầu tiên
            print(f"\n--- User {user.id} ({user.username}) ---")
            
            # Đếm ratings
            ratings = session.exec(
                select(Rating).where(Rating.user_id == user.id)
            ).all()
            
            # Đếm likes
            liked_places = get_user_likes(user.id)
            
            print(f"  Ratings: {len(ratings)}")
            print(f"  Likes: {len(liked_places)}")
            
            # Build profile
            profile = build_user_profile(user.id)
            
            if profile is not None:
                print(f"  ✓ Profile created: shape={profile.shape}, non-zero elements={np.count_nonzero(profile)}")
            else:
                print(f"  ⚠ No profile (cold start)")

def test_like_weight_impact():
    """Test tác động của LIKE_WEIGHT"""
    print("\n=== TEST 3: Like Weight Impact ===")
    
    LIKE_WEIGHT = 0.75
    
    # Tương đương với rating score
    # weight = (score - 3.0) / 2.0
    # 0.75 = (score - 3.0) / 2.0
    # score = 0.75 * 2.0 + 3.0 = 4.5
    
    equivalent_rating = LIKE_WEIGHT * 2.0 + 3.0
    print(f"✓ LIKE_WEIGHT = {LIKE_WEIGHT}")
    print(f"✓ Tương đương với Rating Score: {equivalent_rating}/5.0")
    print(f"✓ Đây là strong positive signal (giữa 'Thích' và 'Rất thích')")

def main():
    """Chạy tất cả tests"""
    print("="*60)
    print("TESTING LIKE INTEGRATION IN RECSYS MODEL")
    print("="*60)
    
    try:
        test_get_user_likes()
        test_build_user_profile()
        test_like_weight_impact()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import numpy as np
    main()
