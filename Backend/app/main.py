from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from app.routers import auth

from app.database import create_db_and_tables

from app.routers import recommendation, rating, chatbot

from app.routers import place



# Define the Lifespan (Startup Event). 
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the app starts: Create tables in .db file (SQLModel)
    create_db_and_tables()
    print("Startup: Database tables created!")
    
    # Khởi tạo RecSys model sau khi database đã sẵn sàng
    from app.routers.recsysmodel import initialize_recsys
    initialize_recsys()
    print("Startup: RecSys model initialized!")
    
    yield
    # This runs when the app stops (optional)
    print("Shutdown: App is stopping")

# Khởi tạo bảng users khi chạy app
# init_db()

app = FastAPI(
    # lifespan is the modern way to define logic that needs to
    # run before your application starts receiving requests (Startup)
    # and after it stops (Shutdown).
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Cấu hình CORS (để tương tác với frontend)
app.add_middleware(
    CORSMiddleware,
    # 1. WHO is allowed to call your API?
    # ["*"] means "Wildcard". ANY website in the world can call your API.
    # In production, you should change this to specific domains like ["https://myapp.com"].
    allow_origins=["*"],

    # 2. Are cookies/passwords allowed?
    # True means the frontend can send cookies or Authorization headers.
    allow_credentials=True,

    # 3. WHAT actions can they perform?
    # ["*"] means they can use GET, POST, PUT, DELETE, PATCH, etc.
    allow_methods=["*"],

    # 4. WHAT extra info can they send?
    # ["*"] means they can send custom headers (like "X-Custom-Header").
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Hello! Backend is running.",
        "docs": "localhost:8000/api/v1/docs", # Added link to docs for convenience
        "admin": "localhost:8000/admin" # Added link to admin for convenience
    }


# @app.get("/health")
# def health():
#     return {"status": "ok"}


# Đăng ký router
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])         # đăng nhập đăng ký
app.include_router(recommendation.router, prefix="/api/v1", tags=["Recommendation"])    # gợi ý địa điểm
app.include_router(rating.router, prefix="/api/v1/user", tags=["User Actions"])         # đánh giá địa điểm

app.include_router(chatbot.router, prefix="/chat", tags=["Chatbot"])         # chatbot

app.include_router(place.router, prefix="/api/v1/place", tags=["Place Details"])        # place details

# admin interface
from app.admin import * 

# Lệnh chạy (nếu chạy trực tiếp python main.py)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
