# Setup môi trường và chạy chương trình

## Trên Windows
  - Dùng `Command Prompt`
### 1. Setup môi trường

#### Nếu đã từng setup môi trường, bỏ qua bước này.

#### Nếu chưa, thực hiện:

  ```terminal
  .env-config\setup.bat
  ```
  - Mở file `.env` trong thư mục `Backend`, điền Groq API key vào ô `key` (lưu ý key nằm trong dấu ngoặc kép `""`).
### 2. Chạy chương trình

  ```terminal
  start.bat
  ```
### 3. Đóng chương trình

  - Khi muốn tắt chương trình, ấn `CTRL + C` trong terminal.
  - Sau đó thực hiện:
    ```terminal
    cd ..
    stop.bat
    ```
# Setup cũ

  - Nếu đã từng setup môi trường, thực hiện bước 4, 6, 7, 8.
  - Sử dụng `Command Prompt` nếu dùng Windows.
## 1. Tạo file .env để điền key API

  - Mở thư mục `.env-config`, nhân bản file `.env.example` sau đó đổi tên thành thành `.env`.
  - Sau đó di chuyển file `.env` vào thư mục `Backend`.

## 2. Điền API key
  - Mở file `.env` trong thư mục `Backend`, điền Groq API key vào ô `key` (lưu ý key nằm trong dấu ngoặc kép `""`).

## 3. Tạo môi trường ảo (Virtual environment)

  - Nếu đã tạo môi trường ảo (có thư mục .venv) thì bỏ qua bước này.
  - Nếu chưa, thực hiện:
    ```terminal
    python -m venv .venv
    ``````terminal
    python -m venv .venv
    ```
## 4. Khởi động môi trường ảo (Virtual environment)

  - Trên WSL, Linux hoặc MacOS:
    ```terminal
    source .venv/bin/activate
    ```
  - Trên Windows:
    ```terminal
    .\.venv\Scripts\activate.bat
    ```
    - Sau khi chạy xong, kiểm tra bằng cách mở `Command Prompt` (KHÔNG PHẢI TERMINAL), nếu thấy có `(.venv)` trước đường dẫn hiện tại thì bật môi trường thành công.

## 5. Tải thêm các gói cần thiết cho môi trường ảo

  - Nếu đã tải các gói trong file `.env-config\requirements.txt` ở môi trường ảo rồi thì bỏ qua bước này.
  - Nếu chưa tải, thực hiện:
    ```terminal
    pip install -r .env-config\requirements.txt
    ```
## 6. Khởi động trang web
  ```terminal
  cd Backend
  uvicorn main:app --reload
  ```
  - Sau khi chạy, chương trình hiện lên 1 đoạn URL, copy dán vào trình duyệt, hoặc `CTRL + chuột trái`.
## 7. Tắt web

  - Khi muốn tắt chương trình, ấn `CTRL + C` trong terminal.
## 8. Tắt môi trường ảo

  - Trên WSL, Linux hoặc MacOS:
    ```terminal

    ```
  - Trên Windows:
    ```terminal
    .\.venv\Scripts\deactivate.bat
    ```

# ?????? 
- Trong terminal sau khi chạy uvicorn main:app --reload nó có bảo unvicorn running on... copy dán vào browser sau đó thêm /api/v1/docs ở đuôi để vào.

