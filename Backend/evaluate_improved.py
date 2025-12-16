"""
Đánh giá improved algorithm (recsysmodel_v2)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Rating, Place
from app.routers import recsysmodel_v2 as recsys
import numpy as np
from collections import defaultdict

# Initialize
print("Initializing improved RecSys...")
recsys.initialize_recsys()
print()

# ==========================================
# EVALUATION LOGIC
# ==========================================

class ImprovedEvaluator:
    def __init__(self):
        self.session = Session(engine)
    
    def create_train_test_split(self, test_ratio=0.2, min_interactions=5):
        """Tạo train/test split"""
        users = self.session.exec(select(User)).all()
        
        train_ratings = []
        test_ratings = []
        test_users = []
        
        for user in users:
            ratings = self.session.exec(
                select(Rating).where(Rating.user_id == user.id)
            ).all()
            
            if len(ratings) < min_interactions:
                continue
            
            # Sort by timestamp if available, else random
            ratings_list = list(ratings)
            np.random.shuffle(ratings_list)
            
            split_idx = int(len(ratings_list) * (1 - test_ratio))
            
            train = ratings_list[:split_idx]
            test = ratings_list[split_idx:]
            
            if len(test) > 0:
                train_ratings.extend(train)
                test_ratings.extend(test)
                test_users.append(user.id)
        
        return train_ratings, test_ratings, test_users
    
    def precision_at_k(self, recommended, relevant, k):
        """Precision@K"""
        top_k = recommended[:k]
        hits = len(set(top_k) & set(relevant))
        return hits / k if k > 0 else 0.0
    
    def recall_at_k(self, recommended, relevant, k):
        """Recall@K"""
        top_k = recommended[:k]
        hits = len(set(top_k) & set(relevant))
        return hits / len(relevant) if len(relevant) > 0 else 0.0
    
    def ndcg_at_k(self, recommended, relevant, k):
        """NDCG@K"""
        top_k = recommended[:k]
        
        dcg = 0.0
        for i, item_id in enumerate(top_k):
            if item_id in relevant:
                dcg += 1.0 / np.log2(i + 2)
        
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant), k)))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def evaluate(self, k_values=[5, 10, 20]):
        """Evaluate toàn bộ"""
        print("Creating train/test split...")
        train_ratings, test_ratings, test_users = self.create_train_test_split()
        
        print(f"✓ Train: {len(train_ratings)} ratings")
        print(f"✓ Test: {len(test_ratings)} ratings")
        print(f"✓ Test users: {len(test_users)}")
        print()
        
        # Group test ratings by user
        test_by_user = defaultdict(list)
        for rating in test_ratings:
            if rating.score >= 3.0:  # Only positive items
                test_by_user[rating.user_id].append(rating.place_id)
        
        # Collect recommendations
        metrics = {k: {'precision': [], 'recall': [], 'ndcg': []} for k in k_values}
        
        print(f"Evaluating {len(test_users)} users...")
        
        for i, user_id in enumerate(test_users):
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(test_users)}] users processed...")
            
            relevant = test_by_user.get(user_id, [])
            
            if len(relevant) == 0:
                continue
            
            # Get recommendations using improved model
            try:
                recs = recsys.recommend_hybrid(user_id, user_tags=[], n=max(k_values))
                recommended_ids = [r['id'] for r in recs]
            except Exception as e:
                print(f"  Error for user {user_id}: {e}")
                continue
            
            # Calculate metrics
            for k in k_values:
                precision = self.precision_at_k(recommended_ids, relevant, k)
                recall = self.recall_at_k(recommended_ids, relevant, k)
                ndcg = self.ndcg_at_k(recommended_ids, relevant, k)
                
                metrics[k]['precision'].append(precision)
                metrics[k]['recall'].append(recall)
                metrics[k]['ndcg'].append(ndcg)
        
        print()
        print("=" * 60)
        print("RESULTS WITH IMPROVED ALGORITHM")
        print("=" * 60)
        print()
        
        for k in k_values:
            print(f"K = {k}:")
            print(f"  Precision@{k}: {np.mean(metrics[k]['precision']) * 100:.2f}%")
            print(f"  Recall@{k}: {np.mean(metrics[k]['recall']) * 100:.2f}%")
            print(f"  NDCG@{k}: {np.mean(metrics[k]['ndcg']) * 100:.2f}%")
            print()
        
        return metrics

if __name__ == "__main__":
    evaluator = ImprovedEvaluator()
    evaluator.evaluate()
