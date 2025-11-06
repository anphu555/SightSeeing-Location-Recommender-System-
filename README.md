### Setup BACKEND API
1. Copy file `.env.example` thành `.env`
2. Điền API key của mình hoặc xin thằng an vào `.env`
3.
  - Chạy trên WSL (Ubuntu) windows gpt đi:
   ```terminal
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
   - Chạy trên Win:
      Trước khi `pip install -r requirements.txt` nhớ comment `uvloop==0.22.1` trong `requirement.txt`
  ```terminal
   python -m venv .venv
   .venv/Script/Activate
   pip install -r requirements.txt
   uvicorn main:app --reload
4. Bật web:
- Trong terminal sau khi chạy uvicorn main:app --reload nó có bảo unvicorn running on... copy dán vào browser sau đó thêm /api/v1/docs ở đuôi để vào.
- Dùng xong `CTRL+C` để thoát và nhớ chạy `deactivate` để tắt môi trường ảo.
