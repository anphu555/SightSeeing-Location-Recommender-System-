"""
TẠO DỮ LIỆU TEST VỚI CATEGORY CONSISTENCY CAO
===============================================

Script này tạo dữ liệu test mới với:
- Users có preferences rõ ràng
- Ratings tập trung vào đúng loại địa điểm trong preferences
- Đảm bảo user thích biển thì rate biển, thích núi thì rate núi

Mục đích: Cải thiện data quality để recommendation system hoạt động tốt hơn
"""

import random
from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Place, Rating
from datetime import datetime
from collections import defaultdict
import json

class ImprovedTestDataGenerator:
    """Tạo dữ liệu test với category consistency cao"""
    
    def __init__(self):
        self.session = Session(engine)
        
        # Load all places
        self.all_places = self.session.exec(select(Place)).all()
        print(f"📊 Loaded {len(self.all_places)} places")
        
        # Group places by tags
        self.places_by_tag = self._group_places_by_tag()
        
        # Define user profiles
        self.user_profiles = self._define_user_profiles()
        
    def _group_places_by_tag(self):
        """Nhóm places theo tags"""
        places_by_tag = defaultdict(list)
        
        for place in self.all_places:
            if not place.tags:
                continue
            
            for tag in place.tags:
                tag_lower = tag.lower()
                places_by_tag[tag_lower].append(place)
        
        print(f"📁 Grouped places into {len(places_by_tag)} tags")
        
        # Print top tags
        sorted_tags = sorted(places_by_tag.items(), key=lambda x: len(x[1]), reverse=True)
        print("   Top 10 tags:")
        for tag, places in sorted_tags[:10]:
            print(f"     - {tag}: {len(places)} places")
        
        return places_by_tag
    
    def _define_user_profiles(self):
        """
        Định nghĩa các user profiles với preferences rõ ràng
        
        Mỗi profile có:
        - name_prefix: Prefix cho username
        - preferences: List tags user thích
        - positive_ratio: Tỉ lệ ratings trong preferences (0.7-0.9)
        - score_range: Range điểm cho places thích (3.5-5.0)
        """
        return [
            {
                'name_prefix': 'beach_lover',
                'preferences': ['beach', 'coastal', 'swimming', 'nature'],
                'positive_ratio': 0.8,  # 80% ratings về beach/coastal
                'description': 'Người thích biển, bãi tắm'
            },
            {
                'name_prefix': 'mountain_explorer',
                'preferences': ['mountain', 'hiking', 'trekking', 'adventure', 'nature'],
                'positive_ratio': 0.8,
                'description': 'Người thích núi, leo núi'
            },
            {
                'name_prefix': 'history_buff',
                'preferences': ['historical', 'cultural', 'architecture', 'museum', 'educational'],
                'positive_ratio': 0.75,
                'description': 'Người thích lịch sử, văn hóa'
            },
            {
                'name_prefix': 'nature_enthusiast',
                'preferences': ['nature', 'peaceful', 'scenic views', 'photography', 'wildlife'],
                'positive_ratio': 0.8,
                'description': 'Người yêu thiên nhiên'
            },
            {
                'name_prefix': 'city_tourist',
                'preferences': ['city', 'entertainment', 'shopping', 'nightlife', 'dining'],
                'positive_ratio': 0.75,
                'description': 'Người thích du lịch thành phố'
            },
            {
                'name_prefix': 'spiritual_seeker',
                'preferences': ['religious', 'temple', 'pagoda', 'spiritual', 'peaceful'],
                'positive_ratio': 0.8,
                'description': 'Người thích đi chùa, tâm linh'
            },
            {
                'name_prefix': 'adventure_junkie',
                'preferences': ['adventure', 'extreme sports', 'rock climbing', 'cave', 'waterfall'],
                'positive_ratio': 0.8,
                'description': 'Người thích mạo hiểm'
            },
            {
                'name_prefix': 'food_traveler',
                'preferences': ['food', 'dining', 'local cuisine', 'street food', 'market'],
                'positive_ratio': 0.75,
                'description': 'Người đi du lịch để ăn uống'
            }
        ]
    
    def _find_matching_places(self, preferences):
        """
        Tìm places matching với preferences
        Ưu tiên places có nhiều tags matching
        """
        place_scores = {}  # place_id -> (place, match_score)
        
        for place in self.all_places:
            if not place.tags:
                continue
            
            place_tags_lower = [t.lower() for t in place.tags]
            
            # Count matching tags
            match_count = 0
            for pref in preferences:
                pref_lower = pref.lower()
                # Check exact match or partial match
                for tag in place_tags_lower:
                    if pref_lower == tag or pref_lower in tag or tag in pref_lower:
                        match_count += 1
                        break  # Count each preference only once per place
            
            if match_count > 0:
                place_scores[place.id] = (place, match_count)
        
        # Sort by match score (higher is better)
        sorted_places = sorted(place_scores.values(), key=lambda x: x[1], reverse=True)
        
        # Return only places (not scores)
        return [place for place, score in sorted_places]
    
    def create_user_with_ratings(self, profile, user_index, num_ratings=15):
        """
        Tạo user với ratings theo profile
        
        Args:
            profile: User profile dict
            user_index: Index để tạo unique username
            num_ratings: Số lượng ratings
        """
        username = f"{profile['name_prefix']}_{user_index:03d}"
        
        # Check if user exists
        existing = self.session.exec(
            select(User).where(User.username == username)
        ).first()
        
        if existing:
            print(f"⚠️  User {username} đã tồn tại")
            return existing
        
        # Create user
        user = User(
            username=username,
            hashed_password="dummy_hash_for_test",
            preferences=profile['preferences'],
            display_name=f"{profile['description']} #{user_index}"
        )
        
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        # Find matching places
        matching_places = self._find_matching_places(profile['preferences'])
        
        if len(matching_places) < 5:
            print(f"⚠️  Không đủ places matching cho {username}, skip ratings")
            return user
        
        # Calculate number of positive (matching) and negative (non-matching) ratings
        num_positive = int(num_ratings * profile['positive_ratio'])
        num_negative = num_ratings - num_positive
        
        # Select places (ưu tiên top matching places)
        # Lấy top 50% matching places để tăng quality
        top_matching = matching_places[:max(len(matching_places)//2, num_positive)]
        positive_places = random.sample(top_matching, min(num_positive, len(top_matching)))
        
        # Select negative places (not in top matching)
        non_matching = [p for p in self.all_places if p not in matching_places[:len(matching_places)//2]]
        negative_places = random.sample(non_matching, min(num_negative, len(non_matching)))
        
        # Create ratings
        for place in positive_places:
            score = random.uniform(3.5, 5.0)  # High scores for matching
            rating = Rating(
                user_id=user.id,
                place_id=place.id,
                score=score
            )
            self.session.add(rating)
        
        for place in negative_places:
            score = random.uniform(1.0, 3.0)  # Low scores for non-matching
            rating = Rating(
                user_id=user.id,
                place_id=place.id,
                score=score
            )
            self.session.add(rating)
        
        self.session.commit()
        
        print(f"✓ Tạo {username}: {len(positive_places)} positive + {len(negative_places)} negative ratings")
        
        return user
    
    def generate_dataset(self, users_per_profile=10):
        """
        Tạo dataset với nhiều users theo từng profile
        
        Args:
            users_per_profile: Số users cho mỗi profile
        """
        print("=" * 80)
        print("BẮT ĐẦU TẠO DỮ LIỆU TEST VỚI CATEGORY CONSISTENCY CAO")
        print("=" * 80)
        print()
        
        total_users = len(self.user_profiles) * users_per_profile
        print(f"📊 Sẽ tạo {total_users} users ({users_per_profile} users x {len(self.user_profiles)} profiles)")
        print()
        
        created = 0
        
        for profile in self.user_profiles:
            print(f"\n📁 Tạo users cho profile: {profile['description']}")
            print(f"   Preferences: {profile['preferences']}")
            print(f"   Positive ratio: {profile['positive_ratio']:.0%}")
            print()
            
            for i in range(users_per_profile):
                try:
                    self.create_user_with_ratings(profile, i + 1)
                    created += 1
                except Exception as e:
                    print(f"❌ Lỗi tạo user: {e}")
        
        print()
        print("=" * 80)
        print(f"✓ HOÀN THÀNH: Đã tạo {created}/{total_users} users")
        print("=" * 80)
        print()
        print("💡 Chạy lại analyze_rating_categories.py để xem kết quả!")
    
    def close(self):
        self.session.close()


def main():
    print("🚀 IMPROVED TEST DATA GENERATOR")
    print()
    
    generator = ImprovedTestDataGenerator()
    
    try:
        # Tạo 5 users cho mỗi profile (tổng 40 users)
        generator.generate_dataset(users_per_profile=5)
    finally:
        generator.close()


if __name__ == "__main__":
    main()
