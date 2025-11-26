import csv
import glob
import requests
import time
import os

output_file = "vietnamPlaces.csv"

# ────────────────────────────────
# Chỉ lấy file CSV ngoại trừ file tổng hợp
# ────────────────────────────────
input_files = [
    f for f in glob.glob("*.csv")
    if os.path.basename(f).lower() not in ["vietnamplaces.csv"]
    if os.path.basename(f).lower() not in ["vietnam_tourism_daily.csv"]
]

print("Các file đang được xử lý:")
for f in input_files:
    print("  -", f)

# ────────────────────────────────
# Hàm phân loại khí hậu theo nhiệt độ
# ────────────────────────────────
def climate_label(temp):
    if temp is None:
        return "unknown"
    if temp >= 32:
        return "extremely hot"
    if temp >= 27:
        return "hot"
    if temp >= 23:
        return "warm"
    if temp >= 17:
        return "cool"
    if temp >= 10:
        return "cold"
    return "extremely cold"


# ────────────────────────────────
# Gọi API khí hậu
# ────────────────────────────────
def fetch_climate(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        r = requests.get(url, timeout=10)
        d = r.json()
        w = d.get("current_weather", {})
        return w.get("temperature"), w.get("windspeed")
    except:
        return None, None


# ────────────────────────────────
# Tạo file output với header chuẩn
# ────────────────────────────────
header = ["name", "kind", "lat", "lon", "province", "temp", "wind", "climate"]

with open(output_file, "w", newline="", encoding="utf-8") as out:
    writer = csv.writer(out)
    writer.writerow(header)

# ────────────────────────────────
# Xử lý từng file CSV
# ────────────────────────────────
with open(output_file, "a", newline="", encoding="utf-8") as out:
    writer = csv.writer(out)

    for file in input_files:
        print("Đang xử lý:", file)

        with open(file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Lấy giá trị an toàn
                lat = row.get("lat") or row.get("Lat") or row.get("LAT")
                lon = row.get("lon") or row.get("Lon") or row.get("LON")
                province = row.get("province/city") or row.get("province")

                # Nếu thiếu dữ liệu → bỏ qua
                if not lat or not lon:
                    print("Bỏ qua row thiếu lat/lon:", row)
                    continue

                temp, wind = fetch_climate(lat, lon)
                label = climate_label(temp)

                writer.writerow([
                    row.get("name"),
                    row.get("kind"),
                    lat,
                    lon,
                    province,
                    temp,
                    wind,
                    label
                ])

                time.sleep(0.25)
