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
