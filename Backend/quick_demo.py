"""
QUICK EVALUATION DEMO
======================

Script đơn giản để test nhanh recommendation system với một vài kịch bản cụ thể.
"""

from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Place, Rating, Like
from app.routers.recsysmodel import recommend_two_tower, initialize_recsys

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")

def demo_recommendation(title: str, tags: list, user_id: int = None, top_k: int = 5):
    """
    Demo một recommendation scenario
    
    Args:
        title: Tiêu đề scenario
        tags: Tags để recommend
        user_id: User ID (optional)
        top_k: Số lượng recommendations
    """
    print(f"🔍 {title}")
    print(f"   Input tags: {tags}")
    print(f"   User ID: {user_id if user_id else 'None (cold-start)'}")
    print()
    
    try:
        results = recommend_two_tower(tags, user_id=user_id, top_k=top_k)
        
        if len(results) == 0:
            print("   ❌ Không có kết quả\n")
            return
        
        print(f"   ✅ Top {min(top_k, len(results))} recommendations:")
        for idx, row in results.iterrows():
            place_tags = row['tags'] if isinstance(row['tags'], list) else []
            print(f"      {idx+1}. {row['name']}")
            print(f"         Score: {row['score']:.3f} | Tags: {', '.join(place_tags[:3])}")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

def show_user_profile(user_id: int, session: Session):
    """Hiển thị profile và history của user"""
    user = session.get(User, user_id)
    
    if not user:
        print(f"❌ User {user_id} không tồn tại\n")
        return
    
    print(f"👤 USER: {user.username} (ID: {user.id})")
    print(f"   Preferences: {user.preferences}")
    
    # Get ratings
    ratings = session.exec(
        select(Rating).where(Rating.user_id == user_id)
    ).all()
    
    print(f"   Ratings: {len(ratings)} places")
    
    if ratings:
        # Show top rated places
        sorted_ratings = sorted(ratings, key=lambda x: x.score, reverse=True)[:3]
        print(f"   Top rated:")
        for rating in sorted_ratings:
            place = session.get(Place, rating.place_id)
            if place:
                print(f"      • {place.name} (score: {rating.score:.1f})")
    
    # Get likes
    likes = session.exec(
        select(Like).where(
            Like.user_id == user_id,
            Like.place_id.isnot(None)
        )
    ).all()
    
    print(f"   Likes: {len(likes)} places")
    print()

def analyze_data_quality(session: Session):
    """Phân tích chất lượng dữ liệu"""
    print_section("📊 DATA QUALITY ANALYSIS")
    
    # Count entities
    users = session.exec(select(User)).all()
    places = session.exec(select(Place)).all()
    ratings = session.exec(select(Rating)).all()
    likes = session.exec(select(Like).where(Like.place_id.isnot(None))).all()
    
    print(f"Total Users: {len(users)}")
    print(f"Total Places: {len(places)}")
    print(f"Total Ratings: {len(ratings)}")
    print(f"Total Likes: {len(likes)}")
    
    # Users with interactions
    users_with_ratings = len(set([r.user_id for r in ratings]))
    users_with_likes = len(set([l.user_id for l in likes]))
    
    print(f"\nUsers with ratings: {users_with_ratings}/{len(users)}")
    print(f"Users with likes: {users_with_likes}/{len(users)}")
    
    # Average interactions per user
    if users_with_ratings > 0:
        avg_ratings = len(ratings) / users_with_ratings
        print(f"Avg ratings per active user: {avg_ratings:.1f}")
    
    # Rating distribution
    if ratings:
        scores = [r.score for r in ratings]
        print(f"\nRating score range: {min(scores):.1f} - {max(scores):.1f}")
        print(f"Average rating: {sum(scores)/len(scores):.2f}")
    
    # Check for cold-start problem
    users_without_interaction = len(users) - max(users_with_ratings, users_with_likes)
    if users_without_interaction > 0:
        print(f"\n⚠️  Cold-start users: {users_without_interaction}")
    
    # Place coverage
    rated_places = len(set([r.place_id for r in ratings]))
    liked_places = len(set([l.place_id for l in likes]))
    
    coverage_rating = (rated_places / len(places) * 100) if places else 0
    coverage_like = (liked_places / len(places) * 100) if places else 0
    
    print(f"\nPlace coverage (ratings): {coverage_rating:.1f}%")
    print(f"Place coverage (likes): {coverage_like:.1f}%")
    
    # Data quality assessment
    print(f"\n{'='*70}")
    
    if len(ratings) < 50:
        print("⚠️  CẢN BÁO: Dữ liệu quá ít!")
        print("   → Cần ít nhất 50+ interactions để đánh giá chính xác")
        print("   → Chạy: python create_test_data.py để tạo synthetic data")
    elif users_with_ratings < 5:
        print("⚠️  CẢN BÁO: Quá ít users có interactions!")
        print("   → Cần ít nhất 5+ active users để đánh giá")
    else:
        print("✅ Dữ liệu đủ để chạy evaluation!")
        print("   → Chạy: python evaluate_recsys.py")

def run_quick_demo():
    """Chạy quick demo"""
    print_section("🚀 QUICK RECOMMENDATION SYSTEM DEMO")
    
    # Initialize
    print("⏳ Initializing recommendation system...")
    initialize_recsys()
    print("✅ Ready!\n")
    
    with Session(engine) as session:
        # Analyze data first
        analyze_data_quality(session)
        
        # Demo scenarios
        print_section("🎯 DEMO SCENARIOS")
        
        # Scenario 1: Cold-start user (no history)
        demo_recommendation(
            "Scenario 1: Cold-start user muốn đi biển",
            tags=["Beach", "Nature"],
            user_id=None,
            top_k=5
        )
        
        # Scenario 2: Cold-start user thích lịch sử
        demo_recommendation(
            "Scenario 2: Cold-start user thích lịch sử",
            tags=["Historical", "Culture", "Hanoi"],
            user_id=None,
            top_k=5
        )
        
        # Scenario 3: User có history
        # Tìm user có nhiều ratings nhất
        ratings_count = {}
        all_ratings = session.exec(select(Rating)).all()
        
        for rating in all_ratings:
            if rating.user_id not in ratings_count:
                ratings_count[rating.user_id] = 0
            ratings_count[rating.user_id] += 1
        
        if ratings_count:
            most_active_user_id = max(ratings_count, key=ratings_count.get)
            
            print_section("👤 USER WITH HISTORY")
            show_user_profile(most_active_user_id, session)
            
            demo_recommendation(
                "Scenario 3: User có history tìm địa điểm mới",
                tags=["Nature", "Adventure"],
                user_id=most_active_user_id,
                top_k=5
            )
        else:
            print("⚠️  Không có user nào có history để demo\n")
        
        # Scenario 4: No input (popular/diverse recommendations)
        demo_recommendation(
            "Scenario 4: Không có input (popular items)",
            tags=[],
            user_id=None,
            top_k=5
        )
        
        print_section("✅ DEMO HOÀN TẤT")
        
        print("📝 NEXT STEPS:")
        print("   1. Tạo test data: python create_test_data.py")
        print("   2. Chạy full evaluation: python evaluate_recsys.py")
        print("   3. Xem kết quả: evaluation_results.json & evaluation_detailed.csv")

if __name__ == "__main__":
    run_quick_demo()
