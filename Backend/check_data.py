from sqlmodel import Session, select
from app.database import engine
from app.schemas import User, Rating, Like

with Session(engine) as session:
    users = session.exec(select(User)).all()
    ratings = session.exec(select(Rating)).all()
    likes = session.exec(select(Like).where(Like.place_id.isnot(None))).all()
    
    print(f"\n📊 DATA SUMMARY:")
    print(f"   Users: {len(users)}")
    print(f"   Ratings: {len(ratings)}")
    print(f"   Likes: {len(likes)}")
    print(f"   Avg ratings/user: {len(ratings)/len(users):.1f}" if users else "")
