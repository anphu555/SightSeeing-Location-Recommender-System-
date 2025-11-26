import pandas as pd
import sqlite3

csv_path = "vietnamPlaces.csv"
db_path = "travel_final.db"
table_name = "sightseeing"

# Các cột cần giữ
desired_cols = ["id", "name", "kind", "lat", "lon", "province", "climate"]

# Đọc CSV
df = pd.read_csv(csv_path, dtype=str)
df.columns = [c.strip() for c in df.columns]

# mapping tên cột
possible_names = {
    "name": "name",
    "kind": "kind",
    "lat": "lat",
    "latitude": "lat",
    "lon": "lon",
    "longitude": "lon",
    "province": "province",
    "province/city": "province",
    "climate": "climate",
    "weather": "climate",
}

col_map = {c: possible_names[c.lower()] for c in df.columns if c.lower() in possible_names}
df = df.rename(columns=col_map)

# tạo id nếu chưa có
df["id"] = range(1, len(df) + 1)

# chỉ giữ đúng 7 cột
for c in desired_cols:
    if c not in df.columns:
        df[c] = None
df_final = df[desired_cols].copy()

# strip text nhẹ
df_final["name"] = df_final["name"].astype(str).str.strip()
df_final["province"] = df_final["province"].astype(str).str.strip()
df_final["climate"] = df_final["climate"].astype(str).str.strip()

# Ghi vào DB
conn = sqlite3.connect(db_path)
df_final.to_sql(table_name, conn, if_exists="replace", index=False)
conn.close()

print(f"[DONE] Đã ghi {len(df_final)} hàng vào {db_path} (bảng: {table_name})")
print(df_final.head(10).to_string(index=False))
