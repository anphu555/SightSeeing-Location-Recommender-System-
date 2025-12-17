import pandas as pd
import json
import numpy as np

# Load evaluation results
df = pd.read_csv('evaluation_detailed.csv')

print("=" * 80)
print("PHÂN TÍCH KẾT QUẢ EVALUATION - THUẬT TOÁN RECOMMENDATION")
print("=" * 80)
print()

# Basic stats
print(f"📊 Tổng số users được đánh giá: {len(df)}")
print(f"📊 Trung bình relevant items/user: {df['num_relevant'].mean():.2f}")
print(f"📊 Min relevant items: {df['num_relevant'].min()}")
print(f"📊 Max relevant items: {df['num_relevant'].max()}")
print()

print("=" * 80)
print("KẾT QUẢ METRICS CHÍNH")
print("=" * 80)
print()

# Precision
print("🎯 PRECISION (Độ chính xác recommendations):")
print(f"   • Precision@5:  {df['precision@5'].mean():.4f} ({df['precision@5'].mean()*100:.2f}%)")
print(f"   • Precision@10: {df['precision@10'].mean():.4f} ({df['precision@10'].mean()*100:.2f}%)")
print(f"   • Precision@20: {df['precision@20'].mean():.4f} ({df['precision@20'].mean()*100:.2f}%)")
print()

# Recall  
print("📈 RECALL (Tỉ lệ tìm được relevant items):")
print(f"   • Recall@5:  {df['recall@5'].mean():.4f} ({df['recall@5'].mean()*100:.2f}%)")
print(f"   • Recall@10: {df['recall@10'].mean():.4f} ({df['recall@10'].mean()*100:.2f}%)")
print(f"   • Recall@20: {df['recall@20'].mean():.4f} ({df['recall@20'].mean()*100:.2f}%)")
print()

# F1
print("⚖️  F1 SCORE (Cân bằng Precision & Recall):")
print(f"   • F1@5:  {df['f1@5'].mean():.4f} ({df['f1@5'].mean()*100:.2f}%)")
print(f"   • F1@10: {df['f1@10'].mean():.4f} ({df['f1@10'].mean()*100:.2f}%)")
print(f"   • F1@20: {df['f1@20'].mean():.4f} ({df['f1@20'].mean()*100:.2f}%)")
print()

# NDCG
print("🏆 NDCG (Ranking Quality):")
print(f"   • NDCG@5:  {df['ndcg@5'].mean():.4f} ({df['ndcg@5'].mean()*100:.2f}%)")
print(f"   • NDCG@10: {df['ndcg@10'].mean():.4f} ({df['ndcg@10'].mean()*100:.2f}%)")
print(f"   • NDCG@20: {df['ndcg@20'].mean():.4f} ({df['ndcg@20'].mean()*100:.2f}%)")
print()

# MAP
print("📊 MAP (Mean Average Precision):")
print(f"   • MAP: {df['map'].mean():.4f} ({df['map'].mean()*100:.2f}%)")
print()

print("=" * 80)
print("PHÂN TÍCH CHI TIẾT")
print("=" * 80)
print()

# Distribution analysis
print("📊 PHÂN PHỐI KẾT QUẢ:")
print(f"   • Users có Precision@5 = 0: {(df['precision@5'] == 0).sum()} ({(df['precision@5'] == 0).sum()/len(df)*100:.1f}%)")
print(f"   • Users có Precision@5 > 0.2: {(df['precision@5'] > 0.2).sum()} ({(df['precision@5'] > 0.2).sum()/len(df)*100:.1f}%)")
print(f"   • Users có Precision@5 > 0.4: {(df['precision@5'] > 0.4).sum()} ({(df['precision@5'] > 0.4).sum()/len(df)*100:.1f}%)")
print()

# Top/Bottom performers
print("🏆 TOP 10 USERS (best Precision@5):")
top10 = df.nlargest(10, 'precision@5')[['user_id', 'precision@5', 'recall@5', 'ndcg@5', 'num_relevant']]
for idx, row in top10.iterrows():
    print(f"   User {row['user_id']:3d}: P@5={row['precision@5']:.3f}, R@5={row['recall@5']:.3f}, NDCG@5={row['ndcg@5']:.3f} ({row['num_relevant']} relevant)")
print()

print("❌ WORST 10 USERS (worst Precision@5):")
worst10 = df.nsmallest(10, 'precision@5')[['user_id', 'precision@5', 'recall@5', 'ndcg@5', 'num_relevant']]
for idx, row in worst10.iterrows():
    print(f"   User {row['user_id']:3d}: P@5={row['precision@5']:.3f}, R@5={row['recall@5']:.3f}, NDCG@5={row['ndcg@5']:.3f} ({row['num_relevant']} relevant)")
print()

# Load JSON results for coverage/diversity
with open('evaluation_results.json', 'r') as f:
    results = json.load(f)

print("=" * 80)
print("COVERAGE & DIVERSITY")
print("=" * 80)
print()
print(f"📊 Coverage (Catalog coverage): {results['coverage']:.4f} ({results['coverage']*100:.2f}%)")
print(f"   → Tỉ lệ items được recommend ít nhất 1 lần")
print()
print(f"🎨 Diversity: {results['diversity']:.4f} ({results['diversity']*100:.2f}%)")
print(f"   → Độ đa dạng trong recommendations")
print()

print("=" * 80)
print("ĐÁNH GIÁ TỔNG QUAN")
print("=" * 80)
print()

avg_p5 = df['precision@5'].mean()
avg_r5 = df['recall@5'].mean()
avg_ndcg5 = df['ndcg@5'].mean()
avg_map = df['map'].mean()

if avg_p5 > 0.3 and avg_r5 > 0.3:
    print("✅ KẾT QUẢ TỐT: Thuật toán hoạt động hiệu quả")
    grade = "A"
elif avg_p5 > 0.2 and avg_r5 > 0.2:
    print("✓ KẾT QUẢ KHÁ: Thuật toán hoạt động tương đối tốt")
    grade = "B"
elif avg_p5 > 0.1 and avg_r5 > 0.1:
    print("⚠️  KẾT QUẢ TRUNG BÌNH: Cần cải thiện thuật toán")
    grade = "C"
else:
    print("❌ KẾT QUẢ YẾU: Cần cải thiện đáng kể")
    grade = "D"

print()
print(f"📝 Xếp loại: {grade}")
print()

print("=" * 80)
print("PHÂN TÍCH NGUYÊN NHÂN")
print("=" * 80)
print()

if avg_p5 < 0.3:
    print("🔍 TẠI SAO KẾT QUẢ CHƯA TỐT?")
    print()
    
    zero_precision = (df['precision@5'] == 0).sum()
    if zero_precision > len(df) * 0.3:
        print(f"1. ❌ {zero_precision}/{len(df)} users ({zero_precision/len(df)*100:.1f}%) có Precision@5 = 0")
        print("   → Model không recommend đúng items user thích")
        print("   → Có thể do:")
        print("      • Data quá sparse (ít interactions)")
        print("      • Features không tốt (tags không phân biệt rõ)")
        print("      • Model chưa học được patterns")
        print()
    
    low_relevant = df['num_relevant'].mean()
    if low_relevant < 5:
        print(f"2. ⚠️  Trung bình chỉ {low_relevant:.1f} relevant items/user")
        print("   → Test set quá nhỏ, khó đánh giá chính xác")
        print("   → Cần thêm dữ liệu interactions")
        print()
    
    if results['coverage'] < 0.3:
        print(f"3. ⚠️  Coverage thấp ({results['coverage']*100:.1f}%)")
        print("   → Model chỉ recommend một số items phổ biến")
        print("   → Thiếu diversity, không explore đủ")
        print()

print("=" * 80)
print("GỢI Ý CẢI THIỆN")
print("=" * 80)
print()

print("💡 HƯỚNG GIẢI QUYẾT:")
print()
print("1. 📊 Cải thiện dữ liệu:")
print("   • Tạo users với preferences rõ ràng hơn")
print("   • Tăng số lượng interactions (ratings/likes)")
print("   • Đảm bảo users rate đúng thể loại (beach → beach)")
print("   → Chạy: python create_improved_test_data.py")
print()

print("2. 🔧 Cải thiện features:")
print("   • Làm sạch tags (loại bỏ tags quá chung như 'sightseeing')")
print("   • Thêm features: location, price, season")
print("   • Sử dụng embeddings từ descriptions")
print()

print("3. 🤖 Cải thiện model:")
print("   • Thử collaborative filtering")
print("   • Hybrid approach (content + collaborative)")
print("   • Fine-tune hyperparameters")
print()

print("4. ✅ Test lại:")
print("   • Sau khi cải thiện, chạy lại evaluation")
print("   • So sánh kết quả với baseline hiện tại")
print()

print("=" * 80)
print("KẾT LUẬN")
print("=" * 80)
print()
print(f"Thuật toán hiện tại đạt Precision@5 = {avg_p5:.2%}, Recall@5 = {avg_r5:.2%}")
print(f"Đây là kết quả {grade} - ", end="")
if grade in ['A', 'B']:
    print("có thể sử dụng được nhưng nên cải thiện thêm")
else:
    print("cần cải thiện đáng kể trước khi deploy production")
print()
print("📝 Report saved to: evaluation_analysis_report.txt")
