"""Xóa test users cũ"""
from sqlmodel import Session, select, delete
from app.database import engine
from app.schemas import User, Rating, Like

with Session(engine) as session:
    users = session.exec(select(User).where(User.username.like('testuser_%'))).all()
    print(f"Tìm thấy {len(users)} test users cần xóa...")
    
    for user in users:
        session.exec(delete(Rating).where(Rating.user_id == user.id))
        session.exec(delete(Like).where(Like.user_id == user.id))
        session.delete(user)
    
    session.commit()
    print(f"✅ Đã xóa {len(users)} test users")
