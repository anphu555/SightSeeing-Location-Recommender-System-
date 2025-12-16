"""
Xóa tất cả users có preferences (old test users)
Chỉ giữ lại users không có preferences (100 users mới)
"""
from sqlmodel import Session, select, delete
from app.database import engine
from app.schemas import User, Rating, Like

with Session(engine) as session:
    # Tìm users có preferences
    all_users = session.exec(select(User)).all()
    
    users_with_prefs = []
    for user in all_users:
        if user.preferences and len(user.preferences) > 0:
            users_with_prefs.append(user)
    
    print(f"Tìm thấy {len(users_with_prefs)} users có preferences")
    print(f"Tổng số users hiện tại: {len(all_users)}")
    
    if users_with_prefs:
        print("\nĐang xóa users có preferences...")
        for user in users_with_prefs:
            # Delete ratings
            session.exec(delete(Rating).where(Rating.user_id == user.id))
            # Delete likes
            session.exec(delete(Like).where(Like.user_id == user.id))
            # Delete user
            session.delete(user)
        
        session.commit()
        print(f"✅ Đã xóa {len(users_with_prefs)} users có preferences")
    
    # Verify
    remaining = session.exec(select(User)).all()
    print(f"\n📊 Còn lại {len(remaining)} users trong database")
    
    # Check preferences
    has_prefs = sum(1 for u in remaining if u.preferences and len(u.preferences) > 0)
    print(f"   - Users có preferences: {has_prefs}")
    print(f"   - Users không có preferences: {len(remaining) - has_prefs}")
