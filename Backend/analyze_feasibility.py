"""
Phân tích khả năng đạt Precision@10 = 40%
"""
from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Rating, Place
import numpy as np

with Session(engine) as session:
    # Thống kê data quality
    users = session.exec(select(User)).all()
    ratings = session.exec(select(Rating)).all()
    places = session.exec(select(Place)).all()
    
    print("=== PHÂN TÍCH DATA QUALITY ===\n")
    print(f"Tổng users: {len(users)}")
    print(f"Tổng ratings: {len(ratings)}")
    print(f"Tổng places: {len(places)}")
    print(f"Sparsity: {len(ratings) / (len(users) * len(places)) * 100:.4f}%")
    
    # Rating distribution
    scores = [r.score for r in ratings]
    print(f"\n📊 Rating Distribution:")
    print(f"  Mean: {np.mean(scores):.2f}")
    print(f"  Median: {np.median(scores):.2f}")
    for score in [1.0, 2.0, 3.0, 4.0, 5.0]:
        count = sum(1 for s in scores if s == score)
        print(f"  Score {score}: {count} ({count/len(scores)*100:.1f}%)")
    
    # Ratings per user
    user_ratings = {}
    for rating in ratings:
        user_ratings[rating.user_id] = user_ratings.get(rating.user_id, 0) + 1
    
    rating_counts = list(user_ratings.values())
    print(f"\n📊 Ratings per User:")
    print(f"  Mean: {np.mean(rating_counts):.1f}")
    print(f"  Median: {np.median(rating_counts):.1f}")
    print(f"  Min: {min(rating_counts)}")
    print(f"  Max: {max(rating_counts)}")
    print(f"  Users with 20+ ratings: {sum(1 for c in rating_counts if c >= 20)}")
    
    # Ratings per place
    place_ratings = {}
    for rating in ratings:
        place_ratings[rating.place_id] = place_ratings.get(rating.place_id, 0) + 1
    
    place_counts = list(place_ratings.values())
    print(f"\n📊 Ratings per Place:")
    print(f"  Mean: {np.mean(place_counts):.1f}")
    print(f"  Median: {np.median(place_counts):.1f}")
    print(f"  Min: {min(place_counts)}")
    print(f"  Max: {max(place_counts)}")
    print(f"  Places with 0 ratings: {len(places) - len(place_ratings)}")
    print(f"  Places with 10+ ratings: {sum(1 for c in place_counts if c >= 10)}")
    
    # Tag analysis
    all_tags = []
    for place in places:
        if place.tags:
            all_tags.extend(place.tags)
    
    unique_tags = set(all_tags)
    print(f"\n📊 Tag Statistics:")
    print(f"  Unique tags: {len(unique_tags)}")
    print(f"  Total tag assignments: {len(all_tags)}")
    print(f"  Avg tags per place: {len(all_tags) / len(places):.1f}")
    
    # Tag co-occurrence (user preferences)
    print(f"\n📊 User Preference Patterns:")
    user_tag_counts = {}
    for rating in ratings:
        if rating.score >= 4.0:
            place = session.get(Place, rating.place_id)
            if place and place.tags:
                if rating.user_id not in user_tag_counts:
                    user_tag_counts[rating.user_id] = {}
                for tag in place.tags:
                    user_tag_counts[rating.user_id][tag] = user_tag_counts[rating.user_id].get(tag, 0) + 1
    
    # Users with clear preferences (one tag appears 3+ times)
    users_with_clear_prefs = 0
    for user_id, tag_counts in user_tag_counts.items():
        if any(count >= 3 for count in tag_counts.values()):
            users_with_clear_prefs += 1
    
    print(f"  Users với clear preferences: {users_with_clear_prefs}/{len(users)} ({users_with_clear_prefs/len(users)*100:.1f}%)")
    
    print("\n=== ĐÁNH GIÁ KHẢ NĂNG ĐẠT 40% ===\n")
    
    # Factors
    print("✅ YẾU TỐ THUẬN LỢI:")
    print(f"  - Data sparsity thấp ({len(ratings) / (len(users) * len(places)) * 100:.4f}%)")
    print(f"  - Có {len(unique_tags)} tags để phân loại")
    print(f"  - {users_with_clear_prefs/len(users)*100:.1f}% users có clear preferences")
    
    print("\n⚠️ YẾU TỐ KHÓ KHĂN:")
    if np.mean(rating_counts) < 15:
        print(f"  - Trung bình chỉ {np.mean(rating_counts):.1f} ratings/user (ít data)")
    if len(places) - len(place_ratings) > 100:
        print(f"  - {len(places) - len(place_ratings)} places chưa có rating (cold-start)")
    print(f"  - Sparsity cao: chỉ {len(ratings) / (len(users) * len(places)) * 100:.4f}% cells có data")
    
    print("\n💡 CHIẾN LƯỢC ĐỀ XUẤT:")
    print("  1. ✅ CẢI THIỆN TF-IDF: n-grams, tag weighting")
    print("  2. ✅ COLLABORATIVE FILTERING: Item-based CF mạnh hơn")
    print("  3. ✅ POPULARITY: Time-decay popularity")
    print("  4. ⭐ MATRIX FACTORIZATION: SVD/ALS cho implicit feedback")
    print("  5. ⭐ DEEP LEARNING: Train Two-Tower model đúng cách")
    print("  6. ⭐ ENSEMBLE: Kết hợp nhiều models")
    print("  7. ✅ RE-RANKING: Diversity + freshness + business rules")
    
    print("\n🎯 KẾT LUẬN:")
    print(f"  Với data hiện tại ({len(ratings)} ratings, {len(users)} users):")
    print(f"  - Precision@10 = 25-30%: ✅ FEASIBLE với cải tiến current approach")
    print(f"  - Precision@10 = 35-40%: ⭐ POSSIBLE với Matrix Factorization hoặc DL")
    print(f"  - Precision@10 = 40%+: ⚠️ CHALLENGING - cần thêm data hoặc context features")
