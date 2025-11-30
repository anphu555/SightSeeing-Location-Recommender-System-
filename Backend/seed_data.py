"""
Script để thêm dữ liệu mẫu vào database
Chạy: python seed_data.py
"""
from sqlmodel import Session
from app.database import engine, create_db_and_tables
from app.schemas import Place

def seed_places():
    """Thêm một số địa điểm mẫu vào database"""
    
    # Tạo tables trước
    create_db_and_tables()
    
    sample_places = [
        Place(
            name="Hạ Long Bay",
            description=["UNESCO World Heritage Site", "Famous for limestone karsts", "Beautiful bay with thousands of islands"],
            image=["halong1.jpg", "halong2.jpg"],
            tags=["Quảng Ninh", "beach", "island", "nature", "UNESCO", "North Vietnam"]
        ),
        Place(
            name="Fansipan Mountain",
            description=["Highest mountain in Vietnam", "Cable car to the summit", "Beautiful mountain scenery"],
            image=["fansipan1.jpg", "fansipan2.jpg"],
            tags=["Lào Cai", "Sapa", "mountain", "hiking", "nature", "cool weather", "North Vietnam"]
        ),
        Place(
            name="Phú Quốc Island",
            description=["Largest island in Vietnam", "Beautiful beaches", "Tropical paradise"],
            image=["phuquoc1.jpg", "phuquoc2.jpg"],
            tags=["Kiên Giang", "island", "beach", "resort", "snorkeling", "South Vietnam"]
        ),
        Place(
            name="Hội An Ancient Town",
            description=["UNESCO World Heritage Site", "Well-preserved ancient town", "Famous for lanterns"],
            image=["hoian1.jpg", "hoian2.jpg"],
            tags=["Quảng Nam", "culture", "history", "ancient", "UNESCO", "Central Vietnam"]
        ),
        Place(
            name="Đà Lạt City",
            description=["City of eternal spring", "Cool weather all year", "Famous for flowers and coffee"],
            image=["dalat1.jpg", "dalat2.jpg"],
            tags=["Lâm Đồng", "city", "mountain", "cool weather", "flowers", "coffee", "Central Highlands"]
        ),
        Place(
            name="Phong Nha-Kẻ Bàng National Park",
            description=["UNESCO World Heritage Site", "World's largest cave", "Amazing cave systems"],
            image=["phongnha1.jpg", "phongnha2.jpg"],
            tags=["Quảng Bình", "cave", "nature", "UNESCO", "adventure", "Central Vietnam"]
        ),
        Place(
            name="Ninh Bình",
            description=["Halong Bay on land", "Limestone karsts and rice fields", "Boat tours through caves"],
            image=["ninhbinh1.jpg", "ninhbinh2.jpg"],
            tags=["Ninh Bình", "nature", "boat", "rice fields", "karst", "North Vietnam"]
        ),
        Place(
            name="Đà Nẵng City",
            description=["Modern coastal city", "Beautiful beaches", "Famous for bridges"],
            image=["danang1.jpg", "danang2.jpg"],
            tags=["Đà Nẵng", "city", "beach", "modern", "bridge", "Central Vietnam"]
        ),
    ]
    
    with Session(engine) as session:
        # Kiểm tra xem đã có data chưa
        from sqlmodel import select
        existing_count = len(session.exec(select(Place)).all())
        
        if existing_count > 0:
            print(f"Database already has {existing_count} places. Skipping seed.")
            return
        
        # Thêm places
        for place in sample_places:
            session.add(place)
        
        session.commit()
        print(f"✅ Successfully added {len(sample_places)} places to database!")

if __name__ == "__main__":
    seed_places()
