#!/bin/bash
# Script để chạy full evaluation: tạo data + test

echo "=== FULL EVALUATION: 100 TEST USERS ==="
echo ""

# Activate venv
source venv/bin/activate

# Step 1: Xóa old test data
echo "Step 1: Xóa old test users..."
python -c "
from sqlmodel import Session, select, delete
from app.database import engine
from app.schemas import User, Rating, Like

with Session(engine) as session:
    # Xóa test users (username starts with 'testuser_')
    users = session.exec(select(User).where(User.username.like('testuser_%'))).all()
    for user in users:
        # Delete ratings
        session.exec(delete(Rating).where(Rating.user_id == user.id))
        # Delete likes
        session.exec(delete(Like).where(Like.user_id == user.id))
        # Delete user
        session.delete(user)
    session.commit()
    print(f'Đã xóa {len(users)} test users')
"

echo ""

# Step 2: Generate new test data
echo "Step 2: Generate 100 test users..."
python generate_100_users.py

echo ""

# Step 3: Run evaluation
echo "Step 3: Run evaluation..."
python evaluate_recsys.py

echo ""
echo "=== DONE ==="
