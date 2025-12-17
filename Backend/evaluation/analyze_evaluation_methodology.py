"""
PHÂN TÍCH PHƯƠNG PHÁP EVALUATION
=================================

Script này giải thích và phân tích cách evaluation được thực hiện,
đặc biệt là cách xác định "relevant items" (ground truth) để tính precision/recall.

VẤN ĐỀ: Làm sao biết được item nào là "relevant" cho user khi chỉ có ratings?
GIẢI ĐÁP: Train/Test Split methodology
"""

import sqlite3
from collections import defaultdict
import json
from pathlib import Path
import numpy as np

class EvaluationMethodologyAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def get_user_interactions(self):
        """Lấy tất cả interactions của users"""
        query = """
        SELECT 
            r.user_id,
            r.place_id,
            r.score,
            p.name as place_name,
            p.tags
        FROM rating r
        JOIN place p ON r.place_id = p.id
        WHERE r.score > 0
        ORDER BY r.user_id, r.score DESC
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        user_interactions = defaultdict(list)
        
        for row in cursor.fetchall():
            try:
                tags = json.loads(row['tags']) if row['tags'] else []
            except:
                tags = []
            
            user_interactions[row['user_id']].append({
                'place_id': row['place_id'],
                'place_name': row['place_name'],
                'score': row['score'],
                'tags': tags
            })
        
        return user_interactions
    
    def simulate_train_test_split(self, user_interactions, test_ratio=0.2):
        """
        Mô phỏng train/test split như trong evaluation
        
        QUAN TRỌNG: Đây là cách xác định "ground truth"!
        - Train set: Model học từ đây
        - Test set: Items này được giấu đi, dùng để đánh giá
        - Ground truth = Test set (những items user thực sự thích nhưng model chưa biết)
        """
        train_data = defaultdict(list)
        test_data = defaultdict(list)
        
        for user_id, interactions in user_interactions.items():
            # Chỉ lấy positive interactions (score >= 3.0)
            positive_interactions = [i for i in interactions if i['score'] >= 3.0]
            
            if len(positive_interactions) < 5:
                continue
            
            # Shuffle
            interactions_copy = positive_interactions.copy()
            np.random.shuffle(interactions_copy)
            
            # Split
            n_test = max(1, int(len(interactions_copy) * test_ratio))
            
            test_data[user_id] = interactions_copy[:n_test]
            train_data[user_id] = interactions_copy[n_test:]
        
        return train_data, test_data
    
    def analyze_evaluation_process(self):
        """Phân tích chi tiết quy trình evaluation"""
        print("=" * 80)
        print("PHÂN TÍCH PHƯƠNG PHÁP EVALUATION")
        print("=" * 80)
        print()
        
        print("📚 GIẢI THÍCH PHƯƠNG PHÁP:")
        print("-" * 80)
        print()
        print("❓ CÂU HỎI: Làm sao biết được item nào là 'relevant' để tính precision/recall?")
        print()
        print("💡 GIẢI ĐÁP: Sử dụng Train/Test Split Methodology")
        print()
        print("🔍 QUY TRÌNH:")
        print()
        print("1. THU THẬP DỮ LIỆU:")
        print("   • Lấy tất cả interactions của user (ratings, likes)")
        print("   • Chỉ giữ POSITIVE interactions (score >= 3.0 hoặc like=True)")
        print("   → Giả định: Score cao = user thích item đó")
        print()
        
        print("2. CHIA DỮ LIỆU (Train/Test Split):")
        print("   • Train set (80%): Model học từ đây")
        print("   • Test set (20%): GIẤU ĐI, dùng để đánh giá")
        print()
        print("   Ví dụ User A thích 10 địa điểm (score >= 3.0):")
        print("   ├─ Train: 8 địa điểm (model biết)")
        print("   └─ Test: 2 địa điểm (GIẤU ĐI - ground truth)")
        print()
        
        print("3. MODEL HỌC VÀ DỰ ĐOÁN:")
        print("   • Model học từ Train set (8 địa điểm)")
        print("   • Model dự đoán top-K recommendations cho User A")
        print("   • Ví dụ: Recommend top-5 = [P1, P2, P3, P4, P5]")
        print()
        
        print("4. ĐÁNH GIÁ (So sánh với Ground Truth):")
        print("   • Ground truth = Test set (2 địa điểm đã giấu)")
        print("   • Kiểm tra: Trong top-5 có bao nhiêu địa điểm thuộc test set?")
        print()
        print("   Nếu top-5 có 1 địa điểm trong test set:")
        print("   ├─ Precision@5 = 1/5 = 0.2 (20% recommendations đúng)")
        print("   ├─ Recall@5 = 1/2 = 0.5 (tìm được 50% relevant items)")
        print("   └─ F1@5 = 2 * (0.2 * 0.5) / (0.2 + 0.5) = 0.286")
        print()
        
        print("=" * 80)
        print("📊 PHÂN TÍCH DỮ LIỆU THỰC TẾ:")
        print("=" * 80)
        print()
        
        # Load và phân tích data
        user_interactions = self.get_user_interactions()
        
        print(f"📈 Tổng số users có interactions: {len(user_interactions)}")
        print()
        
        # Simulate split
        train_data, test_data = self.simulate_train_test_split(user_interactions)
        
        print(f"👥 Users đủ điều kiện cho evaluation: {len(test_data)}")
        print(f"   (Cần ít nhất 5 positive interactions)")
        print()
        
        if not test_data:
            print("⚠️  KHÔNG CÓ DỮ LIỆU ĐỂ PHÂN TÍCH!")
            print("   Cần tạo test data với create_test_data.py trước")
            return
        
        print("=" * 80)
        print("VÍ DỤ CỤ THỂ: Top 5 Users")
        print("=" * 80)
        print()
        
        for i, (user_id, test_items) in enumerate(list(test_data.items())[:5], 1):
            train_items = train_data[user_id]
            
            print(f"{i}. USER {user_id}:")
            print(f"   • Train set: {len(train_items)} items (model biết)")
            print(f"   • Test set: {len(test_items)} items (ground truth - GIẤU ĐI)")
            print()
            
            print(f"   📚 Train items (model học từ đây):")
            for j, item in enumerate(train_items[:3], 1):
                tags_str = ", ".join(item['tags'][:3])
                print(f"      {j}. {item['place_name'][:40]} (score: {item['score']:.1f}) [{tags_str}]")
            if len(train_items) > 3:
                print(f"      ... và {len(train_items) - 3} items khác")
            print()
            
            print(f"   🎯 Test items (ground truth - để đánh giá):")
            for j, item in enumerate(test_items, 1):
                tags_str = ", ".join(item['tags'][:3])
                print(f"      {j}. {item['place_name'][:40]} (score: {item['score']:.1f}) [{tags_str}]")
            print()
            
            # Phân tích tags
            train_tags = defaultdict(int)
            test_tags = defaultdict(int)
            
            for item in train_items:
                for tag in item['tags']:
                    train_tags[tag.lower()] += 1
            
            for item in test_items:
                for tag in item['tags']:
                    test_tags[tag.lower()] += 1
            
            top_train_tags = sorted(train_tags.items(), key=lambda x: x[1], reverse=True)[:3]
            top_test_tags = sorted(test_tags.items(), key=lambda x: x[1], reverse=True)[:3]
            
            print(f"   📊 Top tags trong train: {[f'{t}({c})' for t, c in top_train_tags]}")
            print(f"   📊 Top tags trong test: {[f'{t}({c})' for t, c in top_test_tags]}")
            
            # Check consistency
            train_tag_set = set(train_tags.keys())
            test_tag_set = set(test_tags.keys())
            overlap = len(train_tag_set & test_tag_set) / len(test_tag_set) if test_tag_set else 0
            
            print(f"   ✓ Tag overlap: {overlap:.1%} (test tags cũng xuất hiện trong train)")
            print()
            print("-" * 80)
            print()
        
        print("=" * 80)
        print("💡 ĐÁNH GIÁ TÍNH HỢP LÝ CỦA PHƯƠNG PHÁP:")
        print("=" * 80)
        print()
        
        # Calculate overall statistics
        total_train_items = sum(len(items) for items in train_data.values())
        total_test_items = sum(len(items) for items in test_data.values())
        avg_train = total_train_items / len(train_data) if train_data else 0
        avg_test = total_test_items / len(test_data) if test_data else 0
        
        print(f"📊 THỐNG KÊ TỔNG QUAN:")
        print(f"   • Trung bình train items/user: {avg_train:.1f}")
        print(f"   • Trung bình test items/user: {avg_test:.1f}")
        print(f"   • Tỉ lệ train/test: {avg_train/(avg_train+avg_test):.1%} / {avg_test/(avg_train+avg_test):.1%}")
        print()
        
        # Analyze tag consistency
        tag_overlaps = []
        for user_id, test_items in test_data.items():
            train_items = train_data[user_id]
            
            train_tags = set()
            test_tags = set()
            
            for item in train_items:
                train_tags.update([t.lower() for t in item['tags']])
            
            for item in test_items:
                test_tags.update([t.lower() for t in item['tags']])
            
            if test_tags:
                overlap = len(train_tags & test_tags) / len(test_tags)
                tag_overlaps.append(overlap)
        
        avg_overlap = np.mean(tag_overlaps) if tag_overlaps else 0
        
        print(f"📈 TAG CONSISTENCY:")
        print(f"   • Average tag overlap: {avg_overlap:.1%}")
        print()
        
        if avg_overlap > 0.6:
            print("   ✓ TỐT: Test items có tags tương tự train items")
            print("     → Model có thể học patterns từ train và áp dụng cho test")
            print("     → User thích biển trong train → có thể predict biển trong test")
            print()
        else:
            print("   ⚠️  THẤP: Test items có tags khác xa train items")
            print("     → Khó cho model để generalize")
            print("     → Có thể do user không consistent trong preferences")
            print()
        
        print("=" * 80)
        print("🎯 KẾT LUẬN:")
        print("=" * 80)
        print()
        print("✓ PHƯƠNG PHÁP EVALUATION HỢP LÝ vì:")
        print()
        print("1. Sử dụng Train/Test Split chuẩn trong Machine Learning")
        print("   • Giấu một phần interactions để kiểm tra khả năng dự đoán")
        print("   • Ground truth = Items user thực sự thích (score cao)")
        print()
        print("2. Metrics phù hợp:")
        print("   • Precision@K: % recommendations đúng trong top-K")
        print("   • Recall@K: % relevant items được tìm thấy")
        print("   • NDCG@K: Đánh giá ranking quality")
        print()
        print("3. Giả định hợp lý:")
        print("   • User thích items trong quá khứ (score cao)")
        print("   • → Có thể thích items tương tự trong tương lai")
        print("   • Model học patterns từ train để predict test")
        print()
        
        if avg_overlap > 0.6:
            print("✓ DỮ LIỆU HIỆN TẠI: Phù hợp cho evaluation")
            print("  • Users có preferences tương đối consistent")
            print("  • Model có thể học và generalize được")
        else:
            print("⚠️  DỮ LIỆU HIỆN TẠI: Cần cải thiện")
            print("  • Users không consistent trong preferences")
            print("  • Nên tạo synthetic data với preferences rõ ràng hơn")
            print("  • → Sử dụng create_improved_test_data.py")
        
        print()
        print("=" * 80)
        print("📝 TÓM LẠI:")
        print("=" * 80)
        print()
        print("• Ground truth = Test set (items đã giấu đi)")
        print("• Model KHÔNG biết test items khi training")
        print("• Precision/Recall đo độ chính xác khi dự đoán test items")
        print("• Nếu model recommend đúng test items → Precision/Recall cao")
        print("• Nếu model recommend sai → Precision/Recall thấp")
        print()
    
    def close(self):
        self.conn.close()


def main():
    # Database ở parent directory (backend/)
    db_path = Path(__file__).parent.parent / "vietnamtravel.db"
    
    if not db_path.exists():
        print(f"❌ Không tìm thấy database: {db_path}")
        return
    
    print(f"📂 Database: {db_path}")
    print()
    
    analyzer = EvaluationMethodologyAnalyzer(str(db_path))
    
    try:
        analyzer.analyze_evaluation_process()
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
