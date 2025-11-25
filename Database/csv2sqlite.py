import sqlite3
import pandas as pd

# 1. Kết nối vào file gốc
conn_old = sqlite3.connect('travel.db')

print("Đang đọc dữ liệu từ bảng sightseeing...")

# Lấy toàn bộ dữ liệu thô từ bảng sightseeing
df = pd.read_sql("SELECT * FROM sightseeing", conn_old)

# 2. XỬ LÝ CỘT (Đây là bước làm sạch cấu trúc, không xóa dòng)
# Bảng của bạn bị lỗi dư cột do import sai, ta chỉ lấy 5 cột đầu tiên
df_clean = df.iloc[:, 0:5].copy()

# Đặt lại tên cột cho chuẩn để code backend dễ gọi
df_clean.columns = ['name', 'kind', 'lat', 'lon', 'province']

# 3. THÊM CỘT ID
# Tạo cột id chạy từ 1 đến hết
df_clean.insert(0, 'id', range(1, 1 + len(df_clean)))

print(f"Đã xử lý xong. Tổng số địa điểm: {len(df_clean)}")
print(df_clean.head()) # In thử 5 dòng để bạn kiểm tra

# 4. LƯU RA DATABASE MỚI (travel_final.db)
conn_new = sqlite3.connect('travel_final.db')
df_clean.to_sql('sightseeing', conn_new, if_exists='replace', index=False)

# (Tùy chọn) Nếu bạn muốn copy luôn bảng 'places' sang cho đủ bộ
try:
    df_places = pd.read_sql("SELECT * FROM places", conn_old)
    # Thêm ID cho places luôn nếu cần
    df_places.insert(0, 'id', range(1, 1 + len(df_places)))
    df_places.to_sql('places', conn_new, if_exists='replace', index=False)
    print("Đã copy thêm bảng places.")
except:
    print("Không tìm thấy bảng places hoặc có lỗi.")

conn_old.close()
conn_new.close()

print("\nHoàn tất! File mới là 'travel_final.db'.")