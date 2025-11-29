from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from jose import JWTError, jwt

# Import your configuration and security utils
from app.config import settings
from app.security import verify_password, get_password_hash, create_access_token

# Import your SQLModel classes
from app.schemas import User, UserCreate, UserResponse, Token

# --- DATABASE DEPENDENCY ---
# You likely have this in a separate file (e.g., database.py).
# If so, import it: from app.database import get_session, engine
from sqlmodel import create_engine, Session

# Placeholder engine (replace with your actual engine import)
# engine = create_engine("sqlite:///database.db") 

def get_session():
    with Session(engine) as session:
        yield session

# --- ROUTER SETUP ---
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

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