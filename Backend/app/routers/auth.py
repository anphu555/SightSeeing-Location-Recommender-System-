from datetime import timedelta
from typing import Annotated
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from jose import JWTError, jwt

# Import your configuration and security utils
from app.config import settings
from app.security import verify_password, get_password_hash, create_access_token

# Import your SQLModel classes
from app.schemas import User, UserCreate, UserResponse, Token, UserProfileUpdate

# --- DATABASE DEPENDENCY ---
# You likely have this in a separate file (e.g., database.py).
# If so, import it: from app.database import get_session, engine
from app.database import get_session

from app.services.db_service import create_user, get_user_by_username


# --- ROUTER SETUP ---
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# ==========================================
# 1. REGISTER
# ==========================================
@router.post("/register", response_model=UserResponse)
def register(
    user_input: UserCreate, 
    session: Session = Depends(get_session)
):
    # 1. Check if user exists
    # SQLModel: Use select() + session.exec()
    statement = select(User).where(User.username == user_input.username)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. Hash password
    hashed_pw = get_password_hash(user_input.password)
    
    # 3. Create DB Instance (User Table)
    # Note: We map UserCreate fields to User Table fields here
    db_user = User(
        username=user_input.username, 
        hashed_password=hashed_pw
    )
    
    # 4. Save to DB
    session.add(db_user)
    session.commit()
    session.refresh(db_user) # Important! Gets the generated 'id' back from DB
    
    # 5. Return (FastAPI converts db_user object to UserResponse schema)
    return db_user

# ==========================================
# 2. LOGIN
# ==========================================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # 1. Find user by username
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    
    # 2. Validate User and Password
    # Note: access attributes with dot notation (user.hashed_password), not dict ['key']
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Create Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# 3. GET CURRENT USER (Dependency)
# ==========================================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if token exists
    if not token:
        raise credentials_exception
    
    try:
        # 1. Decode Token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # 2. Fetch User from DB
    # We query the DB to make sure the user still exists and to get their ID
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    
    if user is None:
        raise credentials_exception
        
    # Return the full User object (so we can access user.id in other endpoints)
    return user

async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User | None:
    """
    Tương tự get_current_user nhưng trả về None thay vì raise exception
    Dùng cho các endpoint cho phép anonymous users
    """
    try:
        if not token:
            return None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        # Fetch User from DB
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        
        return user  # Return User object hoặc None
    except:
        return None


# ==========================================
# 4. GET USER PROFILE
# ==========================================
@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Lấy thông tin profile của user hiện tại"""
    return current_user


# ==========================================
# 5. UPDATE USER PROFILE
# ==========================================
@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Cập nhật profile của user (display_name, avatar_url, cover_image_url, bio, location)"""
    
    # Update fields nếu được cung cấp
    if profile_data.display_name is not None:
        current_user.display_name = profile_data.display_name
    
    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url
    
    if profile_data.cover_image_url is not None:
        current_user.cover_image_url = profile_data.cover_image_url
    
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
    
    if profile_data.location is not None:
        current_user.location = profile_data.location
    
    # Save to database
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user


# ==========================================
# 6. UPLOAD AVATAR
# ==========================================
@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Upload avatar image và trả về URL"""
    
    # Kiểm tra file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Kiểm tra file size (max 5MB)
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    for chunk in iter(lambda: file.file.read(chunk_size), b''):
        file_size += len(chunk)
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=400, detail="File size too large. Max 5MB")
    
    # Reset file pointer
    file.file.seek(0)
    
    # Tạo thư mục uploads nếu chưa có
    upload_dir = Path(settings.BACKEND_DIR) / "uploads" / "avatars"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Tạo tên file unique: user_id_timestamp.extension
    import time
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"user_{current_user.id}_{int(time.time())}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Lưu file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Tạo URL để truy cập file
    # Giả sử backend serve static files tại /uploads
    avatar_url = f"/uploads/avatars/{unique_filename}"
    
    # Update user's avatar_url
    current_user.avatar_url = avatar_url
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url,
        "user": UserResponse(
            id=current_user.id,
            username=current_user.username,
            display_name=current_user.display_name,
            avatar_url=current_user.avatar_url,
            cover_image_url=current_user.cover_image_url,
            bio=current_user.bio,
            location=current_user.location,
            preferences=current_user.preferences
        )
    }


# ==========================================
# 7. UPLOAD COVER IMAGE
# ==========================================
@router.post("/upload-cover")
async def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Upload cover image và trả về URL"""
    
    # Kiểm tra file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Kiểm tra file size (max 10MB cho cover image)
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    for chunk in iter(lambda: file.file.read(chunk_size), b''):
        file_size += len(chunk)
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File size too large. Max 10MB")
    
    # Reset file pointer
    file.file.seek(0)
    
    # Tạo thư mục uploads nếu chưa có
    upload_dir = Path(settings.BACKEND_DIR) / "uploads" / "covers"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Tạo tên file unique: cover_user_id_timestamp.extension
    import time
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"cover_{current_user.id}_{int(time.time())}.{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Lưu file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Tạo URL để truy cập file
    cover_url = f"/uploads/covers/{unique_filename}"
    
    # Update user's cover_image_url
    current_user.cover_image_url = cover_url
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {
        "message": "Cover image uploaded successfully",
        "cover_image_url": cover_url,
        "user": UserResponse(
            id=current_user.id,
            username=current_user.username,
            display_name=current_user.display_name,
            avatar_url=current_user.avatar_url,
            cover_image_url=current_user.cover_image_url,
            bio=current_user.bio,
            location=current_user.location,
            preferences=current_user.preferences
        )
    }

    

    