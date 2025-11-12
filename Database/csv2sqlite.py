import pandas as pd
import sqlite3

# Đọc file CSV tổng hợp
df = pd.read_csv("vietnamPlaces.csv")

# Kết nối tới SQLite (tự tạo nếu chưa có)
conn = sqlite3.connect("travel.db")

# Ghi dữ liệu vào bảng 'sightseeing'
df.to_sql("sightseeing", conn, if_exists="replace", index=False)

# Kiểm tra vài dòng
sample = pd.read_sql_query("SELECT * FROM places LIMIT 5;", conn)
print(sample)

conn.close()
print("✅ Đã tạo database travel.db chứa bảng 'sightseeing'!")
