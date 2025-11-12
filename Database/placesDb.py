import requests, csv

# Query: tìm các điểm du lịch trong Ninhbinh
query = """
[out:json][timeout:600];
(
  node["tourism"](10.5,107.5,11.5,108.5);
  way["tourism"](10.5,107.5,11.5,108.5);
  relation["tourism"](10.5,107.5,11.5,108.5);
  node["historic"](10.5,107.5,11.5,108.5);
  node["natural"](10.5,107.5,11.5,108.5);
  node["leisure"="park"](10.5,107.5,11.5,108.5);
);
out center tags;
"""


url = "https://overpass-api.de/api/interpreter"

print("⏳ Đang gửi request đến Overpass API...")
response = requests.post(url, data={'data': query})
response.raise_for_status()
data = response.json()

rows = []
for el in data["elements"]:
    tags = el.get("tags", {})
    name = tags.get("name", "")
    kind = tags.get("tourism") or tags.get("natural") or tags.get("historic") or ""
    lat = el.get("lat") or el.get("center", {}).get("lat")
    lon = el.get("lon") or el.get("center", {}).get("lon")
    if name and lat and lon:
        rows.append([name, kind, lat, lon])

print(f"✅ Lấy được {len(rows)} địa điểm")

# Lưu ra file CSV
with open("places.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "kind", "lat", "lon"])
    writer.writerows(rows)

print("💾 Đã lưu file places.csv thành công!")
