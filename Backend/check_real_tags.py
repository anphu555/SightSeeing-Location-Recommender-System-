"""Check tags thực tế trong database"""
from sqlmodel import Session, select
from app.database import engine
from app.schemas import Place
from collections import Counter

with Session(engine) as session:
    places = session.exec(select(Place)).all()
    
    print(f"Tổng số places: {len(places)}\n")
    
    # Collect all tags
    all_tags = []
    for place in places:
        if place.tags:
            all_tags.extend(place.tags)
    
    # Count frequency
    tag_counts = Counter(all_tags)
    
    print("=" * 70)
    print("TOP 50 TAGS THỰC TẾ TRONG DATABASE")
    print("=" * 70)
    
    for i, (tag, count) in enumerate(tag_counts.most_common(50), 1):
        print(f"{i:3}. {tag:30} ({count} places)")
    
    print(f"\n✓ Tổng số tags unique: {len(tag_counts)}")
