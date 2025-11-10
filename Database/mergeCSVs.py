import pandas as pd
import glob

# Lấy tất cả file CSV trong thư mục hiện tại
files = glob.glob("*.csv")

# Tạo list chứa các DataFrame
dfs = []

for file in files:
    df = pd.read_csv(file)
    dfs.append(df)
    print(f"✅ Đã nạp {file} ({len(df)} dòng)")

# Gộp tất cả DataFrame thành 1 file
merged = pd.concat(dfs, ignore_index=True)

# Ghi ra file tổng hợp
merged.to_csv("vietnamPlaces.csv", index=False, encoding="utf-8")
print(f"🎉 Đã tạo file vietnamPlaces.csv với {len(merged)} dòng dữ liệu!")
