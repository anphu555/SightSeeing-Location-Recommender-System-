from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.schemas import UserCreate, Token, UserResponse
from app.services.db_service import create_user, get_user_by_username
from app.security import verify_password, get_password_hash, create_access_token
from app.config import settings
from datetime import timedelta
from jose import JWTError, jwt

router = APIRouter()
# Thêm auto_error=False để FastAPI không tự động báo lỗi 401 nếu thiếu token
# Điều này cho phép hàm get_current_user_optional xử lý logic "có token thì lấy, không có thì thôi"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    # 1. Check user tồn tại
    if get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. Hash password
    hashed_pw = get_password_hash(user.password)
    
    # 3. Save to DB
    create_user(user.username, hashed_pw)
    
    return UserResponse(username=user.username)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm sẽ lấy username và password từ form gửi lên
    user = get_user_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}



# --- MỚI: Dependency để lấy User hiện tại từ Token ---
# Hàm này sẽ được dùng trong router rating để bảo vệ API
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

async def get_current_user_optional(token: str = Depends(oauth2_scheme)):
    try:
        if not token:
            return None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except:
        return None
