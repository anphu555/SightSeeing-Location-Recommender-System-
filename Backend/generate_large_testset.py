"""
GENERATE LARGE TEST DATASET
Tạo 50+ test users với đa dạng preferences để đánh giá thuật toán
"""

import random
from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Place, Rating, Like
from collections import Counter

# Top real tags from database
PREFERENCE_CATEGORIES = {
    'nature': ['Nature', 'Forest', 'Waterfall', 'Mountains', 'Lake'],
    'beach': ['Beach', 'Coastal', 'Seafood'],
    'history': ['Historical', 'Cultural', 'Architecture', 'Museum'],
    'religion': ['Religious', 'Temple', 'Pagoda', 'Spiritual'],
    'adventure': ['Adventure', 'Hiking', 'Ecotourism', 'Cave'],
    'relaxation': ['Relaxation', 'Peaceful', 'Scenic', 'Scenic Views'],
    'culture': ['Cultural', 'Cultural Heritage', 'Ethnic Culture', 'Festival'],
    'food': ['Local Cuisine', 'Seafood'],
    'family': ['Family-friendly', 'Educational'],
    'wildlife': ['Wildlife', 'Eco-tourism']
}

# Vietnam locations (real tags)
LOCATIONS = [
    'Ha Noi', 'Thua Thien Hue', 'Ho Chi Minh', 'Dien Bien',
    'Bac Giang', 'Bac Ninh', 'Cao Bang', 'Khanh Hoa',
    'Quang Nam', 'Da Nang', 'Binh Dinh', 'Phu Yen',
    'Quang Binh', 'Quang Tri', 'Hung Yen', 'Hai Phong'
]

def generate_user_profiles(num_users=50):
    """Tạo diverse user profiles"""
    profiles = []
    
    # Base names
    name_prefixes = ['test', 'eval', 'demo', 'user']
    
    for i in range(num_users):
        # Random preferences (1-4 categories)
        num_cats = random.randint(1, 4)
        selected_categories = random.sample(list(PREFERENCE_CATEGORIES.keys()), num_cats)
        
        # Build preferences from selected categories
        preferences = []
        for cat in selected_categories:
            # Pick 1-2 tags from each category
            num_tags = random.randint(1, min(2, len(PREFERENCE_CATEGORIES[cat])))
            preferences.extend(random.sample(PREFERENCE_CATEGORIES[cat], num_tags))
        
        # Optionally add location preference (30% chance)
        if random.random() < 0.3:
            preferences.append(random.choice(LOCATIONS))
        
        # Generate username
        category_str = '_'.join(selected_categories[:2])
        username = f"{random.choice(name_prefixes)}_{category_str}_{i+1:03d}"
        
        # Random number of interactions (5-30)
        num_positive = random.randint(5, 30)
        num_negative = random.randint(1, max(2, num_positive // 5))
        
        profiles.append({
            'username': username,
            'preferences': preferences,
            'num_positive': num_positive,
            'num_negative': num_negative
        })
    
    return profiles

def create_user_with_interactions(session, profile, places_by_tag):
    """Tạo user và generate interactions"""
    
    # Check if user exists
    existing = session.exec(
        select(User).where(User.username == profile['username'])
    ).first()
    
    if existing:
        print(f"  ⚠️  {profile['username']} đã tồn tại, skip...")
        return existing
    
    # Create user
    user = User(
        username=profile['username'],
        hashed_password='$2b$12$dummy_hash_for_testing',
        preferences=profile['preferences'],
        display_name=profile['username'].replace('_', ' ').title()
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Find matching places
    matching_places = []
    for pref in user.preferences:
        pref_lower = pref.lower()
        if pref_lower in places_by_tag:
            matching_places.extend(places_by_tag[pref_lower])
    
    # Remove duplicates
    seen_ids = set()
    unique_places = []
    for place in matching_places:
        if place.id not in seen_ids:
            seen_ids.add(place.id)
            unique_places.append(place)
    
    if not unique_places:
        print(f"  ⚠️  Không tìm thấy places cho {user.username}")
        return user
    
    # Get non-matching places
    all_places = []
    for places_list in places_by_tag.values():
        all_places.extend(places_list)
    
    seen_ids_all = set()
    unique_all = []
    for place in all_places:
        if place.id not in seen_ids_all:
            seen_ids_all.add(place.id)
            unique_all.append(place)
    
    non_matching = [p for p in unique_all if p not in unique_places]
    
    # Generate POSITIVE interactions
    num_to_create = min(profile['num_positive'], len(unique_places))
    selected_positive = random.sample(unique_places, num_to_create)
    
    interactions_created = 0
    
    for place in selected_positive:
        # 15% noise
        if random.random() < 0.15 and non_matching:
            place = random.choice(non_matching)
        
        # Random score 3.5-5.0
        score = random.uniform(3.5, 5.0)
        
        rating = Rating(
            user_id=user.id,
            place_id=place.id,
            score=round(score, 2)
        )
        session.add(rating)
        interactions_created += 1
        
        # 40% chance có like
        if random.random() > 0.6:
            like = Like(
                user_id=user.id,
                place_id=place.id,
                is_like=True
            )
            session.add(like)
    
    # Generate NEGATIVE interactions
    if non_matching:
        num_negative = min(profile['num_negative'], len(non_matching))
        selected_negative = random.sample(non_matching, num_negative)
        
        for place in selected_negative:
            # Random score 1.0-2.5
            score = random.uniform(1.0, 2.5)
            
            rating = Rating(
                user_id=user.id,
                place_id=place.id,
                score=round(score, 2)
            )
            session.add(rating)
            
            # 20% chance có dislike
            if random.random() > 0.8:
                dislike = Like(
                    user_id=user.id,
                    place_id=place.id,
                    is_like=False
                )
                session.add(dislike)
    
    session.commit()
    
    return user, interactions_created

def main():
    print(f"\n{'='*70}")
    print("TẠO LARGE TEST DATASET (50+ USERS)")
    print(f"{'='*70}\n")
    
    with Session(engine) as session:
        # Load places
        all_places = session.exec(select(Place)).all()
        print(f"📊 Tổng số places: {len(all_places)}")
        
        if len(all_places) == 0:
            print("❌ Không có places trong database!")
            return
        
        # Group by tags
        places_by_tag = {}
        for place in all_places:
            if not place.tags:
                continue
            for tag in place.tags:
                tag_lower = tag.lower()
                if tag_lower not in places_by_tag:
                    places_by_tag[tag_lower] = []
                places_by_tag[tag_lower].append(place)
        
        print(f"📊 Tags có sẵn: {len(places_by_tag)}\n")
        
        # Generate profiles
        num_users = 50
        profiles = generate_user_profiles(num_users)
        
        print(f"🎯 ĐANG TẠO {num_users} TEST USERS...\n")
        
        total_interactions = 0
        users_created = 0
        
        for i, profile in enumerate(profiles, 1):
            result = create_user_with_interactions(session, profile, places_by_tag)
            
            if isinstance(result, tuple):
                user, num_interactions = result
                total_interactions += num_interactions
                users_created += 1
                
                if i % 10 == 0:
                    print(f"  ✓ Đã tạo {i}/{num_users} users...")
            else:
                if i % 10 == 0:
                    print(f"  ... {i}/{num_users} users processed...")
        
        print(f"\n{'='*70}")
        print("✓ ĐÃ TẠO XONG LARGE TEST DATASET!")
        print(f"{'='*70}\n")
        
        # Statistics
        total_ratings = session.exec(select(Rating)).all()
        total_likes = session.exec(select(Like).where(Like.place_id.isnot(None))).all()
        total_users = session.exec(select(User)).all()
        
        print(f"📊 THỐNG KÊ:")
        print(f"   • Tổng số users: {len(total_users)}")
        print(f"   • Tổng số ratings: {len(total_ratings)}")
        print(f"   • Tổng số likes: {len(total_likes)}")
        print(f"   • Users mới tạo: {users_created}")
        print(f"   • Interactions mới: {total_interactions}")
        
        # Coverage
        rated_places = len(set([r.place_id for r in total_ratings]))
        coverage = (rated_places / len(all_places) * 100) if all_places else 0
        print(f"   • Place coverage: {coverage:.1f}%")
        
        print(f"\n💡 Bây giờ có thể chạy: python evaluate_recsys.py")
        print(f"   Expected evaluation time: ~2-3 minutes với {len(total_users)} users")

if __name__ == "__main__":
    main()
