"""
PHÂN TÍCH CATEGORY CONSISTENCY TRONG USER RATINGS
==================================================

Script này phân tích xem user ratings có tập trung vào cùng một thể loại/category không.
Kiểm tra xem liệu user thích biển thì có rate nhiều địa điểm biển không,
hay có rate lẫn lộn giữa các thể loại.

Mục đích:
- Kiểm tra tính nhất quán (consistency) của user preferences
- Xác định user có "specialized" vào một số category nhất định không
- Tìm các patterns trong behavior của users
"""

import sqlite3
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import json
from pathlib import Path

class CategoryConsistencyAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def get_user_ratings_with_tags(self) -> Dict[int, List[Tuple[int, float, List[str]]]]:
        """
        Lấy tất cả ratings của users kèm theo tags của places
        
        Returns:
            Dict[user_id] -> [(place_id, score, tags), ...]
        """
        query = """
        SELECT 
            r.user_id,
            r.place_id,
            r.score,
            p.tags
        FROM rating r
        JOIN place p ON r.place_id = p.id
        WHERE r.score > 0  -- Chỉ lấy ratings thực sự (> 0)
        ORDER BY r.user_id, r.score DESC
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        user_ratings = defaultdict(list)
        
        for row in cursor.fetchall():
            user_id = row['user_id']
            place_id = row['place_id']
            score = row['score']
            
            # Parse tags từ JSON string
            try:
                tags = json.loads(row['tags']) if row['tags'] else []
            except:
                tags = []
            
            user_ratings[user_id].append((place_id, score, tags))
        
        return user_ratings
    
    def analyze_user_category_distribution(self, user_ratings: Dict) -> Dict:
        """
        Phân tích distribution của categories cho mỗi user
        
        Returns:
            Dict với thông tin phân tích cho từng user
        """
        results = {}
        
        for user_id, ratings in user_ratings.items():
            if len(ratings) < 3:  # Skip users với ít ratings
                continue
            
            # Đếm số lần xuất hiện của mỗi tag
            tag_counts = Counter()
            tag_scores = defaultdict(list)  # Lưu scores cho mỗi tag
            
            total_ratings = len(ratings)
            
            for place_id, score, tags in ratings:
                for tag in tags:
                    tag_lower = tag.lower()
                    tag_counts[tag_lower] += 1
                    tag_scores[tag_lower].append(score)
            
            # Tính metrics
            if not tag_counts:
                continue
                
            # Top categories
            top_categories = tag_counts.most_common(5)
            
            # Diversity score (Shannon entropy normalized)
            # Cao = đa dạng, thấp = tập trung
            total_tags = sum(tag_counts.values())
            diversity = 0
            for count in tag_counts.values():
                p = count / total_tags
                diversity -= p * (p if p == 0 else p * (0 if p == 0 else (1 if p == 1 else (p * 0 if p < 1e-10 else (p * (1 / p) if p > 1 - 1e-10 else (1 - (1 - p) * (1 - p) / 2) if p > 0.5 else p * (1 - p))))))
            
            # Simpler diversity calculation
            import math
            diversity = 0
            for count in tag_counts.values():
                p = count / total_tags
                if p > 0:
                    diversity -= p * math.log2(p)
            
            # Normalize by max possible entropy
            max_entropy = math.log2(len(tag_counts)) if len(tag_counts) > 1 else 1
            normalized_diversity = diversity / max_entropy if max_entropy > 0 else 0
            
            # Concentration score: % ratings trong top category
            concentration = top_categories[0][1] / total_tags if top_categories else 0
            
            # Average score by top category
            avg_scores_by_category = {}
            for tag, _ in top_categories:
                scores = tag_scores[tag]
                avg_scores_by_category[tag] = sum(scores) / len(scores)
            
            results[user_id] = {
                'total_ratings': total_ratings,
                'total_unique_tags': len(tag_counts),
                'top_categories': top_categories,
                'diversity_score': normalized_diversity,  # 0-1, cao = đa dạng
                'concentration_score': concentration,  # 0-1, cao = tập trung
                'avg_scores_by_category': avg_scores_by_category,
                'is_specialized': concentration > 0.5,  # >50% ratings trong 1 category
            }
        
        return results
    
    def get_user_info(self, user_id: int) -> Dict:
        """Lấy thông tin user"""
        query = "SELECT username, preferences FROM user WHERE id = ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        
        if row:
            try:
                preferences = json.loads(row['preferences']) if row['preferences'] else []
            except:
                preferences = []
            
            return {
                'username': row['username'],
                'preferences': preferences
            }
        return None
    
    def print_analysis_report(self):
        """In báo cáo phân tích chi tiết"""
        print("=" * 80)
        print("PHÂN TÍCH CATEGORY CONSISTENCY TRONG USER RATINGS")
        print("=" * 80)
        print()
        
        user_ratings = self.get_user_ratings_with_tags()
        analysis = self.analyze_user_category_distribution(user_ratings)
        
        if not analysis:
            print("⚠️  Không có dữ liệu để phân tích")
            return
        
        print(f"📊 Tổng số users được phân tích: {len(analysis)}")
        print()
        
        # Statistics
        specialized_users = sum(1 for r in analysis.values() if r['is_specialized'])
        diverse_users = len(analysis) - specialized_users
        
        avg_diversity = sum(r['diversity_score'] for r in analysis.values()) / len(analysis)
        avg_concentration = sum(r['concentration_score'] for r in analysis.values()) / len(analysis)
        
        print("📈 TỔNG QUAN:")
        print(f"  • Users tập trung (specialized): {specialized_users} ({specialized_users/len(analysis)*100:.1f}%)")
        print(f"    → Users này >50% ratings tập trung vào 1 category")
        print(f"  • Users đa dạng (diverse): {diverse_users} ({diverse_users/len(analysis)*100:.1f}%)")
        print(f"    → Users này rate nhiều loại địa điểm khác nhau")
        print()
        print(f"  • Diversity score trung bình: {avg_diversity:.3f} (0=tập trung, 1=đa dạng)")
        print(f"  • Concentration score trung bình: {avg_concentration:.3f} (tỉ lệ ratings trong top category)")
        print()
        
        # Sort users by concentration (most specialized first)
        sorted_users = sorted(analysis.items(), key=lambda x: x[1]['concentration_score'], reverse=True)
        
        print("=" * 80)
        print("TOP 10 USERS TẬP TRUNG NHẤT (SPECIALIZED):")
        print("=" * 80)
        
        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user_info = self.get_user_info(user_id)
            username = user_info['username'] if user_info else f"User {user_id}"
            preferences = user_info['preferences'] if user_info else []
            
            print(f"\n{i}. {username} (ID: {user_id})")
            print(f"   Preferences: {preferences}")
            print(f"   Total ratings: {data['total_ratings']}")
            print(f"   Concentration: {data['concentration_score']:.1%} | Diversity: {data['diversity_score']:.3f}")
            print(f"   Top categories:")
            
            for j, (tag, count) in enumerate(data['top_categories'][:3], 1):
                pct = count / data['total_ratings'] * 100
                avg_score = data['avg_scores_by_category'].get(tag, 0)
                print(f"      {j}. {tag}: {count} ratings ({pct:.1f}%) - avg score: {avg_score:.2f}")
        
        print()
        print("=" * 80)
        print("TOP 10 USERS ĐA DẠNG NHẤT (DIVERSE):")
        print("=" * 80)
        
        # Sort by diversity score
        sorted_diverse = sorted(analysis.items(), key=lambda x: x[1]['diversity_score'], reverse=True)
        
        for i, (user_id, data) in enumerate(sorted_diverse[:10], 1):
            user_info = self.get_user_info(user_id)
            username = user_info['username'] if user_info else f"User {user_id}"
            preferences = user_info['preferences'] if user_info else []
            
            print(f"\n{i}. {username} (ID: {user_id})")
            print(f"   Preferences: {preferences}")
            print(f"   Total ratings: {data['total_ratings']}")
            print(f"   Diversity: {data['diversity_score']:.3f} | Concentration: {data['concentration_score']:.1%}")
            print(f"   Top categories:")
            
            for j, (tag, count) in enumerate(data['top_categories'][:3], 1):
                pct = count / data['total_ratings'] * 100
                avg_score = data['avg_scores_by_category'].get(tag, 0)
                print(f"      {j}. {tag}: {count} ratings ({pct:.1f}%) - avg score: {avg_score:.2f}")
        
        print()
        print("=" * 80)
        print("PHÂN TÍCH PREFERENCE MATCHING:")
        print("=" * 80)
        print("Kiểm tra xem user có rate đúng loại địa điểm trong preferences không")
        print()
        
        matched = 0
        not_matched = 0
        
        for user_id, data in analysis.items():
            user_info = self.get_user_info(user_id)
            if not user_info or not user_info['preferences']:
                continue
            
            preferences_lower = [p.lower() for p in user_info['preferences']]
            top_category = data['top_categories'][0][0] if data['top_categories'] else None
            
            if top_category and any(pref in top_category or top_category in pref for pref in preferences_lower):
                matched += 1
            else:
                not_matched += 1
                
                # Print mismatched cases
                if not_matched <= 10:  # Chỉ in 10 cases đầu
                    print(f"❌ {user_info['username']} (ID: {user_id})")
                    print(f"   Preferences: {user_info['preferences']}")
                    print(f"   Top rated category: {top_category} ({data['top_categories'][0][1]} ratings)")
                    print()
        
        total_with_pref = matched + not_matched
        if total_with_pref > 0:
            print(f"📊 Tổng kết:")
            print(f"  • Users rate đúng preferences: {matched} ({matched/total_with_pref*100:.1f}%)")
            print(f"  • Users rate khác preferences: {not_matched} ({not_matched/total_with_pref*100:.1f}%)")
        
        print()
        print("=" * 80)
        print("💡 KẾT LUẬN VÀ KHUYẾN NGHỊ:")
        print("=" * 80)
        
        if avg_concentration > 0.5:
            print("✓ Dữ liệu TỐT: Users có xu hướng rate tập trung vào một số categories nhất định")
            print("  → Hệ thống recommendation có thể hoạt động hiệu quả")
            print("  → User thích biển thì sẽ được recommend biển (như bạn test)")
        else:
            print("⚠️  Dữ liệu CẦN CẢI THIỆN: Users rate khá đa dạng, không tập trung")
            print("  → Có thể khó để xác định preferences rõ ràng")
            print("  → Cần thêm dữ liệu hoặc cải thiện cách collect interactions")
        
        print()
        
        if not_matched > matched:
            print("⚠️  LƯU Ý: Nhiều users rate khác với preferences đã set")
            print("  → Có thể preferences không phản ánh đúng sở thích")
            print("  → Hoặc users khám phá nhiều loại địa điểm khác nhau")
        else:
            print("✓ TỐT: Phần lớn users rate đúng với preferences đã set")
            print("  → Preferences phản ánh tốt sở thích thực tế")
        
        print()
    
    def close(self):
        self.conn.close()


def main():
    # Database ở parent directory (backend/)
    db_path = Path(__file__).parent.parent / "vietnamtravel.db"
    
    if not db_path.exists():
        print(f"❌ Không tìm thấy database: {db_path}")
        return
    
    print(f"📂 Đang phân tích database: {db_path}")
    print()
    
    analyzer = CategoryConsistencyAnalyzer(str(db_path))
    
    try:
        analyzer.print_analysis_report()
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
