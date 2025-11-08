@echo off
REM Activate the virtual environment (venv). 
CALL .\.venv\Scripts\activate.bat

REM Change to the Backend directory to use uvicorn
cd Backend

REM Start the server
uvicorn main:app --reload