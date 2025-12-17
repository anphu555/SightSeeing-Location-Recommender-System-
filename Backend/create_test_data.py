"""
SYNTHETIC TEST DATA GENERATOR
===============================

Script này tạo dữ liệu test giả lập (synthetic data) để đánh giá recommendation system
khi dữ liệu thực tế chưa đủ.

Tạo các user profiles với preferences rõ ràng và tạo interactions phù hợp.
"""

import random
from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Place, Rating, Like
from datetime import datetime

class SyntheticDataGenerator:
    """Tạo dữ liệu test giả lập"""
    
    def __init__(self, session: Session):
        self.session = session
        
        # Load all places
        self.all_places = session.exec(select(Place)).all()
        self.places_by_tag = self._group_places_by_tag()
        
    def _group_places_by_tag(self):
        """Nhóm places theo tags"""
        places_by_tag = {}
        
        for place in self.all_places:
            if not place.tags:
                continue
            
            for tag in place.tags:
                tag_lower = tag.lower()
                if tag_lower not in places_by_tag:
                    places_by_tag[tag_lower] = []
                places_by_tag[tag_lower].append(place)
        
        return places_by_tag
    
    def create_synthetic_user(self, username: str, preferences: list, hashed_password: str = "dummy_hash"):
        """
        Tạo synthetic user với preferences
        
        Args:
            username: Username
            preferences: List tags user thích (vd: ["Beach", "Nature"])
            hashed_password: Hash password (dummy cho test)
        """
        # Check if user exists
        existing = self.session.exec(
            select(User).where(User.username == username)
        ).first()
        
        if existing:
            print(f"⚠️  User {username} đã tồn tại, skip...")
            return existing
        
        user = User(
            username=username,
            hashed_password=hashed_password,
            preferences=preferences,
            display_name=username.title()
        )
        
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        print(f"✓ Tạo user: {username} (preferences: {preferences})")
        
        return user
    
    def generate_interactions_for_user(
        self,
        user: User,
        num_positive: int = 10,
        num_negative: int = 3,
        noise_ratio: float = 0.2
    ):
        """
        Tạo interactions cho user dựa trên preferences
        
        Args:
            user: User object
            num_positive: Số interactions positive (score cao)
            num_negative: Số interactions negative (score thấp)
            noise_ratio: Tỉ lệ noise (interactions không match preferences)
        """
        # Get places matching user preferences
        matching_places = []
        
        for pref in user.preferences:
            pref_lower = pref.lower()
            if pref_lower in self.places_by_tag:
                matching_places.extend(self.places_by_tag[pref_lower])
        
        # Remove duplicates (by place ID)
        seen_ids = set()
        unique_places = []
        for place in matching_places:
            if place.id not in seen_ids:
                seen_ids.add(place.id)
                unique_places.append(place)
        matching_places = unique_places
        
        if not matching_places:
            print(f"⚠️  Không tìm thấy places matching preferences của {user.username}")
            return
        
        # Get non-matching places (cho negative examples)
        non_matching_places = [p for p in self.all_places if p not in matching_places]
        
        # Generate POSITIVE interactions
        num_to_create = min(num_positive, len(matching_places))
        selected_positive = random.sample(matching_places, num_to_create)
        
        for place in selected_positive:
            # Add noise: 20% chance không match preferences
            if random.random() < noise_ratio and non_matching_places:
                place = random.choice(non_matching_places)
            
            # Random score từ 3.5 - 5.0 (positive)
            score = random.uniform(3.5, 5.0)
            
            # Check if rating exists
            existing_rating = self.session.exec(
                select(Rating).where(
                    Rating.user_id == user.id,
                    Rating.place_id == place.id
                )
            ).first()
            
            if not existing_rating:
                rating = Rating(
                    user_id=user.id,
                    place_id=place.id,
                    score=round(score, 2)
                )
                self.session.add(rating)
            
            # Random: 50% chance có like
            if random.random() > 0.5:
                existing_like = self.session.exec(
                    select(Like).where(
                        Like.user_id == user.id,
                        Like.place_id == place.id
                    )
                ).first()
                
                if not existing_like:
                    like = Like(
                        user_id=user.id,
                        place_id=place.id,
                        is_like=True
                    )
                    self.session.add(like)
        
        # Generate NEGATIVE interactions
        if non_matching_places:
            num_to_create = min(num_negative, len(non_matching_places))
            selected_negative = random.sample(non_matching_places, num_to_create)
            
            for place in selected_negative:
                # Random score từ 1.0 - 2.5 (negative)
                score = random.uniform(1.0, 2.5)
                
                existing_rating = self.session.exec(
                    select(Rating).where(
                        Rating.user_id == user.id,
                        Rating.place_id == place.id
                    )
                ).first()
                
                if not existing_rating:
                    rating = Rating(
                        user_id=user.id,
                        place_id=place.id,
                        score=round(score, 2)
                    )
                    self.session.add(rating)
        
        self.session.commit()
        print(f"  → Tạo {num_to_create} positive + {min(num_negative, len(non_matching_places))} negative interactions")

def create_test_dataset():
    """
    Tạo bộ test data hoàn chỉnh với nhiều user profiles khác nhau
    """
    print(f"\n{'='*60}")
    print("TẠO SYNTHETIC TEST DATASET")
    print(f"{'='*60}\n")
    
    with Session(engine) as session:
        generator = SyntheticDataGenerator(session)
        
        # Kiểm tra số lượng places
        num_places = len(generator.all_places)
        print(f"📊 Tổng số places trong DB: {num_places}")
        
        if num_places == 0:
            print("✗ Không có places trong database!")
            print("💡 Hãy chạy seed_data.py trước")
            return
        
        # Hiển thị tags có sẵn
        available_tags = list(generator.places_by_tag.keys())
        print(f"📊 Tags có sẵn: {len(available_tags)}")
        print(f"   Top tags: {', '.join(available_tags[:10])}\n")
        
        # Define test user profiles (CHỈ DÙNG TAGS THỰC TẾ TỪ DATABASE)
        test_profiles = [
            {
                "username": "test_beach_lover",
                "preferences": ["Beach", "Coastal", "Nature"],
                "num_positive": 12,
                "num_negative": 3
            },
            {
                "username": "test_history_buff",
                "preferences": ["Historical", "Cultural", "Ha Noi"],
                "num_positive": 10,
                "num_negative": 4
            },
            {
                "username": "test_mountain_hiker",
                "preferences": ["Mountains", "Hiking", "Nature"],
                "num_positive": 15,
                "num_negative": 2
            },
            {
                "username": "test_food_explorer",
                "preferences": ["Local Cuisine", "Cultural", "Seafood"],
                "num_positive": 8,
                "num_negative": 5
            },
            {
                "username": "test_adventure_traveler",
                "preferences": ["Adventure", "Nature", "Ecotourism"],
                "num_positive": 10,
                "num_negative": 3
            },
            {
                "username": "test_relaxation_seeker",
                "preferences": ["Relaxation", "Peaceful", "Beach"],
                "num_positive": 7,
                "num_negative": 2
            },
            {
                "username": "test_diverse_user",
                "preferences": ["Beach", "Mountains", "Historical", "Temple"],
                "num_positive": 20,
                "num_negative": 5
            },
            {
                "username": "test_nature_lover",
                "preferences": ["Nature", "Forest", "Waterfall"],
                "num_positive": 12,
                "num_negative": 2
            }
        ]
        
        print(f"ĐANG TẠO {len(test_profiles)} TEST USERS...\n")
        
        for profile in test_profiles:
            # Create user
            user = generator.create_synthetic_user(
                username=profile["username"],
                preferences=profile["preferences"]
            )
            
            # Generate interactions
            generator.generate_interactions_for_user(
                user=user,
                num_positive=profile["num_positive"],
                num_negative=profile["num_negative"],
                noise_ratio=0.15  # 15% noise
            )
            
            print()
        
        print(f"{'='*60}")
        print("✓ ĐÃ TẠO XONG SYNTHETIC TEST DATASET!")
        print(f"{'='*60}\n")
        
        # Statistics
        total_ratings = session.exec(select(Rating)).all()
        total_likes = session.exec(select(Like).where(Like.place_id.isnot(None))).all()
        
        print(f"📊 THỐNG KÊ:")
        print(f"   • Tổng số ratings: {len(total_ratings)}")
        print(f"   • Tổng số likes: {len(total_likes)}")
        print(f"   • Test users: {len(test_profiles)}")
        print(f"\n💡 Bây giờ có thể chạy: python evaluate_recsys.py")

if __name__ == "__main__":
    create_test_dataset()
