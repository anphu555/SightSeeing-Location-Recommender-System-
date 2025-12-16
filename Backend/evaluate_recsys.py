"""
EVALUATION FRAMEWORK CHO HỆ THỐNG ĐỀ XUẤT (RECOMMENDATION SYSTEM)
=====================================================================

Framework này đánh giá độ chính xác của thuật toán đề xuất dựa trên:
1. Precision@K, Recall@K, F1@K
2. Mean Average Precision (MAP)
3. Normalized Discounted Cumulative Gain (NDCG)
4. Coverage & Diversity
5. Cold-start performance

Author: Evaluation System
Date: December 16, 2025
"""

import pandas as pd
import numpy as np
from sqlmodel import Session, select
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import json

import sys
import os
# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine
from app.schemas import User, Place, Rating, Like
from app.routers.recsysmodel import recommend_two_tower, initialize_recsys

# ==========================================
# 1. TẠO TEST SET
# ==========================================

class TestSetGenerator:
    """Tạo test set từ dữ liệu hiện có"""
    
    def __init__(self, session: Session):
        self.session = session
        self.train_ratings = []
        self.test_ratings = []
        
    def create_train_test_split(self, test_ratio=0.2, min_interactions=5):
        """
        Tạo train/test split theo Leave-One-Out hoặc Random Split
        
        Args:
            test_ratio: Tỉ lệ dữ liệu để test (0.2 = 20%)
            min_interactions: User phải có ít nhất n interactions để được đưa vào test
            
        Returns:
            train_data, test_data
        """
        # Lấy tất cả ratings và likes
        all_ratings = self.session.exec(select(Rating)).all()
        all_likes = self.session.exec(select(Like).where(Like.place_id.isnot(None))).all()
        
        # Tổng hợp interactions theo user
        user_interactions = defaultdict(list)
        
        # Từ ratings (score >= 3.0 coi là positive)
        for rating in all_ratings:
            if rating.score >= 3.0:
                user_interactions[rating.user_id].append({
                    'user_id': rating.user_id,
                    'place_id': rating.place_id,
                    'score': rating.score,
                    'type': 'rating'
                })
        
        # Từ likes (is_like=True coi là positive)
        for like in all_likes:
            if like.is_like:
                user_interactions[like.user_id].append({
                    'user_id': like.user_id,
                    'place_id': like.place_id,
                    'score': 5.0,  # Like = score cao nhất
                    'type': 'like'
                })
        
        # Lọc users có đủ interactions
        qualified_users = {
            user_id: interactions 
            for user_id, interactions in user_interactions.items() 
            if len(interactions) >= min_interactions
        }
        
        print(f"✓ Tổng số users: {len(user_interactions)}")
        print(f"✓ Users có đủ {min_interactions}+ interactions: {len(qualified_users)}")
        
        # Split data
        train_data = []
        test_data = []
        
        for user_id, interactions in qualified_users.items():
            # Shuffle để random
            interactions = list(interactions)
            np.random.shuffle(interactions)
            
            # Tính số lượng test items
            n_test = max(1, int(len(interactions) * test_ratio))
            
            test_data.extend(interactions[:n_test])
            train_data.extend(interactions[n_test:])
        
        self.train_ratings = train_data
        self.test_ratings = test_data
        
        print(f"✓ Train set: {len(train_data)} interactions")
        print(f"✓ Test set: {len(test_data)} interactions")
        print(f"✓ Test users: {len(set([t['user_id'] for t in test_data]))}")
        
        return train_data, test_data
    
    def get_ground_truth(self) -> Dict[int, List[int]]:
        """
        Lấy ground truth: Danh sách places mà mỗi user thực sự thích
        
        Returns:
            Dict[user_id] = [place_id1, place_id2, ...]
        """
        ground_truth = defaultdict(list)
        
        for item in self.test_ratings:
            ground_truth[item['user_id']].append(item['place_id'])
        
        return dict(ground_truth)

# ==========================================
# 2. METRICS ĐÁNH GIÁ
# ==========================================

class RecommendationMetrics:
    """Các metrics để đánh giá recommendation system"""
    
    @staticmethod
    def precision_at_k(recommended: List[int], relevant: List[int], k: int) -> float:
        """
        Precision@K: Tỉ lệ items được đề xuất là relevant
        
        Formula: (# relevant items in top-k) / k
        """
        if k == 0:
            return 0.0
        
        recommended_k = recommended[:k]
        relevant_set = set(relevant)
        
        hits = len([item for item in recommended_k if item in relevant_set])
        return hits / k
    
    @staticmethod
    def recall_at_k(recommended: List[int], relevant: List[int], k: int) -> float:
        """
        Recall@K: Tỉ lệ relevant items được tìm thấy trong top-k
        
        Formula: (# relevant items in top-k) / (total # relevant items)
        """
        if len(relevant) == 0:
            return 0.0
        
        recommended_k = recommended[:k]
        relevant_set = set(relevant)
        
        hits = len([item for item in recommended_k if item in relevant_set])
        return hits / len(relevant)
    
    @staticmethod
    def f1_at_k(recommended: List[int], relevant: List[int], k: int) -> float:
        """
        F1@K: Harmonic mean của Precision@K và Recall@K
        """
        precision = RecommendationMetrics.precision_at_k(recommended, relevant, k)
        recall = RecommendationMetrics.recall_at_k(recommended, relevant, k)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def average_precision(recommended: List[int], relevant: List[int]) -> float:
        """
        Average Precision (AP): Trung bình precision tại mỗi relevant item
        
        Formula: (1/|relevant|) * Σ(Precision@k * rel(k))
        """
        if len(relevant) == 0:
            return 0.0
        
        relevant_set = set(relevant)
        score = 0.0
        num_hits = 0.0
        
        for i, item in enumerate(recommended):
            if item in relevant_set:
                num_hits += 1.0
                precision_at_i = num_hits / (i + 1.0)
                score += precision_at_i
        
        return score / len(relevant)
    
    @staticmethod
    def ndcg_at_k(recommended: List[int], relevant: List[int], k: int) -> float:
        """
        Normalized Discounted Cumulative Gain (NDCG@K)
        Đánh giá ranking quality: items relevant ở vị trí cao hơn = tốt hơn
        
        Formula: DCG@K / IDCG@K
        """
        def dcg(scores: List[float], k: int) -> float:
            """Discounted Cumulative Gain"""
            scores_k = scores[:k]
            return sum([
                (2**score - 1) / np.log2(i + 2)  # i+2 vì index bắt đầu từ 0
                for i, score in enumerate(scores_k)
            ])
        
        # Tạo relevance scores (1 nếu relevant, 0 nếu không)
        relevant_set = set(relevant)
        scores = [1.0 if item in relevant_set else 0.0 for item in recommended]
        
        # DCG của recommended list
        dcg_score = dcg(scores, k)
        
        # IDCG (ideal DCG): sắp xếp tất cả relevant items lên đầu
        ideal_scores = [1.0] * min(len(relevant), k) + [0.0] * max(0, k - len(relevant))
        idcg_score = dcg(ideal_scores, k)
        
        if idcg_score == 0:
            return 0.0
        
        return dcg_score / idcg_score
    
    @staticmethod
    def coverage(all_recommended: List[List[int]], total_items: int) -> float:
        """
        Coverage: Tỉ lệ items được đề xuất ít nhất 1 lần
        
        Formula: (# unique items recommended) / (total # items)
        """
        unique_items = set()
        for rec_list in all_recommended:
            unique_items.update(rec_list)
        
        return len(unique_items) / total_items if total_items > 0 else 0.0
    
    @staticmethod
    def diversity(all_recommended: List[List[int]]) -> float:
        """
        Diversity: Đo độ đa dạng của các recommendations
        Tính bằng average pairwise distance giữa các items
        
        Ở đây dùng phương pháp đơn giản: unique items / total recommended items
        """
        total_items = 0
        unique_items = set()
        
        for rec_list in all_recommended:
            total_items += len(rec_list)
            unique_items.update(rec_list)
        
        return len(unique_items) / total_items if total_items > 0 else 0.0

# ==========================================
# 3. EVALUATOR CHÍNH
# ==========================================

class RecommendationEvaluator:
    """Class chính để đánh giá recommendation system"""
    
    def __init__(self, session: Session):
        self.session = session
        self.metrics = RecommendationMetrics()
        
    def evaluate_user(
        self, 
        user_id: int, 
        ground_truth: List[int],
        k_values: List[int] = [5, 10, 20]
    ) -> Dict:
        """
        Đánh giá cho 1 user cụ thể
        
        Args:
            user_id: ID của user
            ground_truth: List places mà user thực sự thích (từ test set)
            k_values: Các giá trị K để đánh giá
            
        Returns:
            Dict chứa các metrics
        """
        # Lấy user preferences (từ history)
        user = self.session.get(User, user_id)
        if not user:
            return None
        
        # Lấy tags từ ratings history (score >= 3.0)
        statement = select(Rating).where(Rating.user_id == user_id, Rating.score >= 3.0)
        ratings = self.session.exec(statement).all()
        
        user_tags = []
        for rating in ratings:
            place = self.session.get(Place, rating.place_id)
            if place and place.tags:
                user_tags.extend(place.tags)
        
        # KHÔNG dùng preferences trong evaluation (realistic test)
        # Chỉ dùng actual behavior (ratings/likes)
        
        # Remove duplicates
        user_tags = list(set(user_tags))
        
        # Nếu không có tags, dùng popular recommendations
        if not user_tags:
            user_tags = []
        
        # Gọi recommendation model
        try:
            recommendations_df = recommend_two_tower(
                user_prefs_tags=user_tags,
                user_id=user_id,
                top_k=max(k_values)  # Lấy top-K lớn nhất
            )
            
            recommended_ids = recommendations_df['id'].tolist()
        except Exception as e:
            print(f"✗ Error recommending for user {user_id}: {e}")
            return None
        
        # Tính metrics cho từng K
        results = {'user_id': user_id}
        
        for k in k_values:
            results[f'precision@{k}'] = self.metrics.precision_at_k(recommended_ids, ground_truth, k)
            results[f'recall@{k}'] = self.metrics.recall_at_k(recommended_ids, ground_truth, k)
            results[f'f1@{k}'] = self.metrics.f1_at_k(recommended_ids, ground_truth, k)
            results[f'ndcg@{k}'] = self.metrics.ndcg_at_k(recommended_ids, ground_truth, k)
        
        results['map'] = self.metrics.average_precision(recommended_ids, ground_truth)
        results['num_relevant'] = len(ground_truth)
        results['num_recommended'] = len(recommended_ids)
        
        return results
    
    def evaluate_all(
        self,
        ground_truth_dict: Dict[int, List[int]],
        k_values: List[int] = [5, 10, 20]
    ) -> Dict:
        """
        Đánh giá toàn bộ test set
        
        Args:
            ground_truth_dict: Dict[user_id] = [relevant_place_ids]
            k_values: Các giá trị K để đánh giá
            
        Returns:
            Dict chứa aggregate metrics
        """
        all_results = []
        all_recommended = []
        
        print(f"\n{'='*60}")
        print(f"ĐANG ĐÁNH GIÁ {len(ground_truth_dict)} USERS...")
        print(f"{'='*60}\n")
        
        for i, (user_id, relevant_places) in enumerate(ground_truth_dict.items(), 1):
            print(f"[{i}/{len(ground_truth_dict)}] User {user_id}: {len(relevant_places)} relevant places")
            
            result = self.evaluate_user(user_id, relevant_places, k_values)
            
            if result:
                all_results.append(result)
                
                # Lưu recommendations để tính coverage/diversity
                user = self.session.get(User, user_id)
                if user:
                    user_tags = []
                    statement = select(Rating).where(Rating.user_id == user_id, Rating.score >= 3.0)
                    ratings = self.session.exec(statement).all()
                    for rating in ratings:
                        place = self.session.get(Place, rating.place_id)
                        if place and place.tags:
                            user_tags.extend(place.tags)
                    
                    # KHÔNG dùng preferences - chỉ actual behavior
                    
                    user_tags = list(set(user_tags))
                    
                    try:
                        recs_df = recommend_two_tower(user_tags, user_id, max(k_values))
                        all_recommended.append(recs_df['id'].tolist())
                    except:
                        pass
        
        if not all_results:
            print("✗ Không có kết quả đánh giá nào!")
            return {}
        
        # Tính aggregate metrics
        df_results = pd.DataFrame(all_results)
        
        aggregate = {
            'num_users_evaluated': len(all_results),
            'avg_relevant_per_user': df_results['num_relevant'].mean(),
        }
        
        # Average metrics
        for k in k_values:
            aggregate[f'avg_precision@{k}'] = df_results[f'precision@{k}'].mean()
            aggregate[f'avg_recall@{k}'] = df_results[f'recall@{k}'].mean()
            aggregate[f'avg_f1@{k}'] = df_results[f'f1@{k}'].mean()
            aggregate[f'avg_ndcg@{k}'] = df_results[f'ndcg@{k}'].mean()
        
        aggregate['avg_map'] = df_results['map'].mean()
        
        # Coverage & Diversity
        total_places = self.session.exec(select(Place)).all()
        aggregate['coverage'] = self.metrics.coverage(all_recommended, len(total_places))
        aggregate['diversity'] = self.metrics.diversity(all_recommended)
        
        return aggregate, df_results

# ==========================================
# 4. MAIN EVALUATION SCRIPT
# ==========================================

def run_evaluation(test_ratio=0.2, min_interactions=5, k_values=[5, 10, 20]):
    """
    Chạy full evaluation pipeline
    
    Args:
        test_ratio: Tỉ lệ data cho test set
        min_interactions: Số interactions tối thiểu của user
        k_values: Các giá trị K để đánh giá
    """
    print(f"\n{'='*60}")
    print(f"HỆ THỐNG ĐÁNH GIÁ RECOMMENDATION ALGORITHM")
    print(f"{'='*60}\n")
    
    # Khởi tạo RecSys model
    print("⏳ Đang khởi tạo Recommendation Model...")
    initialize_recsys()
    print("✓ Model đã sẵn sàng!\n")
    
    # Tạo session
    with Session(engine) as session:
        # Bước 1: Tạo test set
        print("BƯỚC 1: TẠO TRAIN/TEST SPLIT")
        print("-" * 60)
        
        generator = TestSetGenerator(session)
        train_data, test_data = generator.create_train_test_split(
            test_ratio=test_ratio,
            min_interactions=min_interactions
        )
        
        if not test_data:
            print("✗ Không đủ dữ liệu để tạo test set!")
            print("💡 Gợi ý: Cần có ít nhất 1 user với >= 5 interactions (ratings/likes)")
            return None
        
        ground_truth = generator.get_ground_truth()
        
        # Bước 2: Chạy evaluation
        print(f"\nBƯỚC 2: ĐÁNH GIÁ VỚI K = {k_values}")
        print("-" * 60)
        
        evaluator = RecommendationEvaluator(session)
        aggregate_results, detailed_results = evaluator.evaluate_all(ground_truth, k_values)
        
        # Bước 3: Hiển thị kết quả
        print(f"\n{'='*60}")
        print(f"KẾT QUẢ ĐÁNH GIÁ TỔNG HỢP")
        print(f"{'='*60}\n")
        
        print(f"📊 Số users được đánh giá: {aggregate_results['num_users_evaluated']}")
        print(f"📊 Trung bình relevant items/user: {aggregate_results['avg_relevant_per_user']:.2f}\n")
        
        print("📈 PRECISION (Độ chính xác của đề xuất):")
        for k in k_values:
            score = aggregate_results[f'avg_precision@{k}'] * 100
            print(f"   • Precision@{k}: {score:.2f}%")
        
        print("\n📈 RECALL (Tỉ lệ items relevant được tìm thấy):")
        for k in k_values:
            score = aggregate_results[f'avg_recall@{k}'] * 100
            print(f"   • Recall@{k}: {score:.2f}%")
        
        print("\n📈 F1 SCORE (Harmonic mean of Precision & Recall):")
        for k in k_values:
            score = aggregate_results[f'avg_f1@{k}'] * 100
            print(f"   • F1@{k}: {score:.2f}%")
        
        print("\n📈 NDCG (Ranking Quality):")
        for k in k_values:
            score = aggregate_results[f'avg_ndcg@{k}'] * 100
            print(f"   • NDCG@{k}: {score:.2f}%")
        
        map_score = aggregate_results['avg_map'] * 100
        print(f"\n📈 MAP (Mean Average Precision): {map_score:.2f}%")
        
        coverage = aggregate_results['coverage'] * 100
        diversity = aggregate_results['diversity'] * 100
        print(f"\n📈 COVERAGE (Catalog coverage): {coverage:.2f}%")
        print(f"📈 DIVERSITY (Recommendation diversity): {diversity:.2f}%")
        
        # Đánh giá chất lượng
        print(f"\n{'='*60}")
        print("💡 ĐÁNH GIÁ CHẤT LƯỢNG THUẬT TOÁN")
        print(f"{'='*60}\n")
        
        # Tiêu chí đánh giá (industry standards)
        avg_precision_10 = aggregate_results['avg_precision@10']
        avg_ndcg_10 = aggregate_results['avg_ndcg@10']
        
        if avg_precision_10 >= 0.3 and avg_ndcg_10 >= 0.4:
            quality = "🌟 XUẤT SẮC"
        elif avg_precision_10 >= 0.2 and avg_ndcg_10 >= 0.3:
            quality = "✅ TỐT"
        elif avg_precision_10 >= 0.1 and avg_ndcg_10 >= 0.2:
            quality = "⚠️ TRUNG BÌNH"
        else:
            quality = "❌ CẦN CẢI THIỆN"
        
        print(f"Kết luận: {quality}")
        
        if quality == "❌ CẦN CẢI THIỆN":
            print("\n💡 Gợi ý cải thiện:")
            print("   1. Thu thập thêm dữ liệu user interactions")
            print("   2. Cải thiện feature engineering (tags, descriptions)")
            print("   3. Thử các thuật toán khác (collaborative filtering, hybrid)")
            print("   4. Fine-tune hyperparameters")
        
        # Lưu kết quả
        print(f"\n{'='*60}")
        print("💾 ĐANG LƯU KẾT QUẢ...")
        print(f"{'='*60}\n")
        
        # Lưu aggregate results
        with open('evaluation_results.json', 'w', encoding='utf-8') as f:
            json.dump(aggregate_results, f, indent=2, ensure_ascii=False)
        print("✓ Đã lưu: evaluation_results.json")
        
        # Lưu detailed results
        detailed_results.to_csv('evaluation_detailed.csv', index=False, encoding='utf-8')
        print("✓ Đã lưu: evaluation_detailed.csv")
        
        return aggregate_results, detailed_results

# ==========================================
# 5. COLD-START EVALUATION
# ==========================================

def evaluate_cold_start():
    """
    Đánh giá hiệu suất với cold-start users (users mới, không có history)
    """
    print(f"\n{'='*60}")
    print("ĐÁNH GIÁ COLD-START PERFORMANCE")
    print(f"{'='*60}\n")
    
    initialize_recsys()
    
    # Test scenarios cho cold-start users
    test_queries = [
        {"tags": ["Hanoi", "Historical"], "description": "User mới thích lịch sử Hà Nội"},
        {"tags": ["Beach", "Nha Trang"], "description": "User mới muốn đi biển Nha Trang"},
        {"tags": ["Mountain", "Nature"], "description": "User mới thích núi và thiên nhiên"},
        {"tags": ["Food", "Culture"], "description": "User mới quan tâm ẩm thực văn hóa"},
        {"tags": [], "description": "User mới không có preferences"}
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query['description']}")
        print(f"Tags: {query['tags']}")
        
        try:
            results = recommend_two_tower(query['tags'], user_id=None, top_k=5)
            print(f"✓ Trả về {len(results)} recommendations")
            print(f"  Places: {', '.join(results['name'].tolist()[:3])}...\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")

# ==========================================
# RUN EVALUATION
# ==========================================

if __name__ == "__main__":
    # Full evaluation
    results = run_evaluation(
        test_ratio=0.2,
        min_interactions=5,
        k_values=[5, 10, 20]
    )
    
    # Cold-start evaluation
    evaluate_cold_start()
