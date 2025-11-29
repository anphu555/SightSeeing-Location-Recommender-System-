# app/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt #, JWTError
import bcrypt  # <--- Thay đổi: Import bcrypt trực tiếp
from app.config import settings

# Xóa dòng pwd_context = CryptContext(...)

def verify_password(plain_password, hashed_password):
    # Bcrypt yêu cầu dữ liệu dạng bytes, nên cần .encode('utf-8')
    # hashed_password từ DB là string, cần encode sang bytes
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password):
    # Tạo salt và hash password
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # Trả về string để lưu vào Database (SQLite TEXT)
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt