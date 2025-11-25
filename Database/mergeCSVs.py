import pandas as pd
import glob

# ⚠️ LỌC BỎ CÁC FILE ĐẦU RA và các file không phải CSV
# Điều này ngăn file tổng hợp cũ (có thể bị trống/hỏng) tự gộp vào chính nó.
EXCLUDED_FILES = ["vietnamPlaces.csv", "places.csv", "travel.db"] 

# Lấy tất cả file CSV trong thư mục hiện tại
all_files = glob.glob("*.csv")

# Lọc bỏ các file đầu ra khỏi danh sách
files_to_merge = [f for f in all_files if f not in EXCLUDED_FILES]

# Tạo list chứa các DataFrame
dfs = []

print(f"Tổng cộng {len(files_to_merge)} file nguồn sẽ được gộp:")

for file in files_to_merge:
    try:
        # Thử đọc file
        df = pd.read_csv(file)
        dfs.append(df)
        print(f"✅ Đã nạp {file} ({len(df)} dòng)")
    except pd.errors.EmptyDataError:
        # Xử lý trường hợp file trống
        print(f"⚠️ CẢNH BÁO: File {file} bị trống hoặc không có cột để đọc. Đã bỏ qua.")
        continue

# Gộp tất cả DataFrame thành 1 file
merged = pd.concat(dfs, ignore_index=True)

# Ghi ra file tổng hợp (Lệnh này tự động xóa nội dung cũ và ghi nội dung mới)
merged.to_csv("vietnamPlaces.csv", index=False, encoding="utf-8")
print(f"\n🎉 Đã tạo file vietnamPlaces.csv thành công với {len(merged)} dòng dữ liệu!")