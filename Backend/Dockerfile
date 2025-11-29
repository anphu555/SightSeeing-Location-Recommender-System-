# backend/Dockerfile
FROM python:3.10-slim

# Đặt thư mục làm việc
# Docker sẽ tự động tạo một thư mục tên là /code bên trong cái "thùng hàng" (container) và chui vào đó đứng.
WORKDIR /code

# Copy file thư viện vào trước (để tận dụng cache của Docker)
COPY requirements.txt .

# Cài đặt thư viện
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code còn lại vào
COPY . .

# Lệnh chạy server
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]