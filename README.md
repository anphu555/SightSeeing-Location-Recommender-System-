# Setup môi trường và chạy chương trình

## Trên Windows

  - Dùng `Command Prompt`
  - Di chuyển đến thư mục chính
### 1. Setup môi trường

#### Nếu đã từng setup môi trường, bỏ qua bước này.

#### Nếu chưa, thực hiện:

  ```bash
  .env-config\setup.bat
  ```
  - Mở file `.env` trong thư mục `Backend`, điền Groq API key vào ô `key` (lưu ý key nằm trong dấu ngoặc kép `""`).
### 2. Chạy chương trình

  ```bash
  start.bat
  ```
### 3. Đóng chương trình

  - Khi muốn tắt chương trình, ấn `CTRL + C` trong terminal.
  - Sau đó thực hiện:
    ```bash
    cd ..
    stop.bat
    ```

## Trên Linux

  - Di chuyển đến thư mục chính
### 1. Setup môi trường

#### Nếu đã từng setup môi trường, bỏ qua bước này.

#### Nếu chưa, thực hiện:

  ```bash
  ./.env-config/setup.sh
  ```
  - Mở file `.env` trong thư mục `Backend`, điền Groq API key vào ô `key` (lưu ý key nằm trong dấu ngoặc kép `""`).
### 2. Chạy chương trình

  ```terminal
  ./start.sh
  ```
### 3. Đóng chương trình

  - Khi muốn tắt chương trình, ấn `CTRL + C` trong terminal.
  - Sau đó thực hiện:
    ```bash
    cd ..
    ./stop.bat
    ```

## Chạy bằng docker:
# 1. Tải docker (nhớ tải bản 2.x đừng tải bản 1.x):
- https://www.docker.com/products/docker-desktop/
# 2. Build và chạy:
- `sudo docker compose up --build` (linux)
- `docker compose up --build` (window)
- Sau khi build xong thì truy cập `localhost:3000` để vào trang web, `localhost:8000/api/v1/docs` để vào swagger UI (backend)
# 3. Thoát
- `CTRL + C`

### Cách chạy web bằng node (nếu muốn test chung backend thì chạy start.bat hay start.sh như thường)
## Frontend:
# 1. Tải node:
- nodejs.org
# 2. Vào thư mục exSighting
-  cd frontend/exSighting/ 
# 3. Chạy lệnh: (cái này chỉ cần làm 1 lần, cả linux lẫn window)
- `npm install`
# 4. Mở web bằng lệnh:
- `npm run dev`

# 📊 User Rating & Scoring Algorithm

A comprehensive algorithm that tracks user interactions and calculates personalized scores for places.

## Quick Links
- **[Quick Reference](backend/SCORING_QUICK_REFERENCE.md)** - Get started in 5 minutes
- **[Complete Documentation](backend/SCORING_ALGORITHM.md)** - Full reference guide
- **[Implementation Summary](backend/IMPLEMENTATION_SUMMARY.md)** - What was built
- **[Flow Diagrams](backend/SCORING_FLOW_DIAGRAM.md)** - Visual architecture

## Features
- ✅ Automatic search tracking (+0.5 per appearance)
- ✅ Watch time tracking (-2/+1/+2 based on duration)
- ✅ Like/Dislike (10.0 or 1.0)
- ✅ Cumulative scoring (0.0-10.0 scale)
- ✅ RESTful API endpoints
- ✅ Frontend integration examples

## Quick Test
```bash
cd backend
python -m app.services.test_scoring_algorithm
```

See documentation above for complete details and integration guide.

---

# Update database
## B1: Thay model trong alembic/env.py (chỗ import schemas dòng 9)
## B1: Chạy cái này
```bash 
alembic revision --autogenerate -m "message"
alembic upgrade head
```
## B2: Chạy cái này