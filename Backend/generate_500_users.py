"""
Generate 500 test users với realistic behavior patterns
Increase data size để improve recommendation quality
"""

from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Rating, Like, Place
import random
import string

def get_real_tags():
    """Lấy danh sách tags thực từ database"""
    with Session(engine) as session:
        places = session.exec(select(Place)).all()
        all_tags = set()
        for place in places:
            if place.tags:
                all_tags.update(place.tags)
        return list(all_tags)

def generate_username():
    """Tạo random username"""
    return f"testuser_{random.randint(100000, 999999)}"

def get_places_by_tag_optimized(all_places, tag):
    """Lấy places có tag cụ thể (optimized - không query DB)"""
    return [p for p in all_places if p.tags and tag in p.tags]

def generate_realistic_user_behavior(session, user_id, all_tags, all_places):
    """
    Tạo realistic user behavior:
    - Chọn 2-5 tags "yêu thích" (implicit preferences thông qua behavior)
    - Rate/like các places có những tags đó
    - Thỉnh thoảng rate/like random places (explore behavior)
    - Rating distribution realistic (nhiều rating 4-5, ít rating 1-2)
    - Varying engagement levels (some users rate many, some few)
    """
    
    # User engagement level (some active, some passive)
    engagement = random.choice(['low', 'medium', 'high'])
    
    if engagement == 'low':
        num_favorite_tags = random.randint(2, 3)
        num_ratings = random.randint(8, 15)
        num_likes = random.randint(3, 8)
    elif engagement == 'medium':
        num_favorite_tags = random.randint(2, 4)
        num_ratings = random.randint(15, 25)
        num_likes = random.randint(8, 15)
    else:  # high
        num_favorite_tags = random.randint(3, 5)
        num_ratings = random.randint(25, 40)
        num_likes = random.randint(15, 25)
    
    # Chọn favorite tags
    favorite_tags = random.sample(all_tags, num_favorite_tags)
    
    # Lấy places có favorite tags (optimized)
    favorite_places = []
    for tag in favorite_tags:
        places = get_places_by_tag_optimized(all_places, tag)
        favorite_places.extend(places)
    
    # Remove duplicates
    favorite_places = list({p.id: p for p in favorite_places}.values())
    
    if not favorite_places:
        favorite_places = random.sample(all_places, min(30, len(all_places)))
    
    # Tạo ratings: 70% từ favorite places, 30% random (explore)
    rated_places = set()
    ratings_to_create = []
    
    # 70% ratings cho favorite places
    num_favorite_ratings = int(num_ratings * 0.7)
    if favorite_places and num_favorite_ratings > 0:
        sample_size = min(num_favorite_ratings, len(favorite_places))
        favorite_sample = random.sample(favorite_places, sample_size)
        
        for place in favorite_sample:
            # Ratings cho favorite places: skewed towards 4-5
            score = random.choices(
                [3.0, 4.0, 5.0],
                weights=[0.2, 0.4, 0.4]
            )[0]
            
            ratings_to_create.append({
                'place_id': place.id,
                'score': score
            })
            rated_places.add(place.id)
    
    # 30% ratings cho random places (exploration)
    num_explore_ratings = num_ratings - len(ratings_to_create)
    if num_explore_ratings > 0:
        available_places = [p for p in all_places if p.id not in rated_places]
        if available_places:
            sample_size = min(num_explore_ratings, len(available_places))
            explore_sample = random.sample(available_places, sample_size)
            
            for place in explore_sample:
                # Explore ratings: more diverse
                score = random.choices(
                    [2.0, 3.0, 4.0, 5.0],
                    weights=[0.1, 0.3, 0.4, 0.2]
                )[0]
                
                ratings_to_create.append({
                    'place_id': place.id,
                    'score': score
                })
                rated_places.add(place.id)
    
    # Tạo ratings trong database
    for rating_data in ratings_to_create:
        rating = Rating(
            user_id=user_id,
            place_id=rating_data['place_id'],
            score=rating_data['score']
        )
        session.add(rating)
    
    # Tạo likes: ưu tiên places đã rate cao
    high_rated = [r for r in ratings_to_create if r['score'] >= 4.0]
    liked_places = set()
    
    # 60% likes cho high-rated places
    if high_rated:
        num_high_likes = min(int(num_likes * 0.6), len(high_rated))
        for rating_data in random.sample(high_rated, num_high_likes):
            like = Like(
                user_id=user_id,
                place_id=rating_data['place_id'],
                is_like=True
            )
            session.add(like)
            liked_places.add(rating_data['place_id'])
    
    # 40% likes cho places khác
    remaining_likes = num_likes - len(liked_places)
    if remaining_likes > 0:
        available = [p for p in all_places if p.id not in liked_places and p.id not in rated_places]
        if available:
            sample_size = min(remaining_likes, len(available))
            for place in random.sample(available, sample_size):
                like = Like(
                    user_id=user_id,
                    place_id=place.id,
                    is_like=True
                )
                session.add(like)
    
    return favorite_tags, engagement

def generate_500_test_users():
    """Generate 500 test users với realistic behavior"""
    
    print("=== GENERATE 500 TEST USERS ===\n")
    print("Đang load tags và places từ database...")
    
    all_tags = get_real_tags()
    print(f"Tìm thấy {len(all_tags)} unique tags")
    
    with Session(engine) as session:
        all_places = session.exec(select(Place)).all()
        print(f"Tìm thấy {len(all_places)} places")
        
        if len(all_places) < 20:
            print("CẢNH BÁO: Quá ít places trong database!")
            return
        
        print(f"\nĐang tạo 500 test users...")
        print("(Sẽ mất vài phút...)")
        print()
        
        created_count = 0
        engagement_stats = {'low': 0, 'medium': 0, 'high': 0}
        
        for i in range(500):
            # Tạo user
            username = generate_username()
            email = f"{username}@test.com"
            
            # Check xem username đã tồn tại chưa
            existing = session.exec(select(User).where(User.username == username)).first()
            if existing:
                continue
            
            # Tạo user KHÔNG CÓ preferences
            user = User(
                username=username,
                email=email,
                hashed_password="dummy_hash_for_test",
                preferences=[]  # KHÔNG set preferences
            )
            session.add(user)
            session.flush()  # Để lấy user.id
            
            # Tạo realistic behavior
            favorite_tags, engagement = generate_realistic_user_behavior(
                session, 
                user.id, 
                all_tags, 
                all_places
            )
            
            engagement_stats[engagement] += 1
            created_count += 1
            
            if (i + 1) % 50 == 0:
                print(f"  [{i + 1}/500] Đã tạo {i + 1} users...")
                session.commit()  # Commit mỗi 50 users
        
        session.commit()
        print(f"\n✅ Hoàn thành! Đã tạo {created_count} test users")
        
        # Statistics
        print("\n📊 Thống kê:")
        total_ratings = session.exec(select(Rating)).all()
        total_likes = session.exec(select(Like)).all()
        test_users = session.exec(select(User).where(User.username.like("testuser_%"))).all()
        
        print(f"  - Tổng test users: {len(test_users)}")
        print(f"  - User engagement:")
        print(f"    • Low: {engagement_stats['low']} users")
        print(f"    • Medium: {engagement_stats['medium']} users")
        print(f"    • High: {engagement_stats['high']} users")
        print(f"  - Tổng ratings: {len(total_ratings)}")
        print(f"  - Tổng likes: {len(total_likes)}")
        print(f"  - Trung bình ratings/user: {len(total_ratings)/len(test_users):.1f}")
        print(f"  - Trung bình likes/user: {len(total_likes)/len(test_users):.1f}")
        print(f"  - Sparsity: {100 * len(total_ratings) / (len(test_users) * len(all_places)):.4f}%")

if __name__ == "__main__":
    generate_500_test_users()
