import pandas as pd

df = pd.read_csv("places.csv")

# def map_category(kind):
#     kind = str(kind).lower()
#     if kind in ["beach", "viewpoint", "island", "cave", "mountain", "peak", "cave_entrance"]:
#         return "nature"
#     elif kind in ["museum", "temple", "church", "monument", "memorial", "castle", "battlefield", "archaeological_site"]:
#         return "culture"
#     elif kind in ["hotel", "guest_house", "resort", "chalet", "motel", "hostel"]:
#         return "accommodation"
#     elif kind in ["restaurant", "cafe", "bar"]:
#         return "food"
#     elif kind in ["park", "theme_park", "zoo", "attraction"]:
#         return "entertainment"
#     else:
#         return "other"

# df["category"] = df["kind"].apply(map_category)

df["province/city"] = "Bình Thuận"

df.to_csv("binhthuan.csv", index=False, encoding="utf-8")
print("✅ File mới có thêm cột province/city đã được lưu!")
