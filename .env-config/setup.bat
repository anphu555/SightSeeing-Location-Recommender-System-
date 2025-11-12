@echo off

@REM Make sure python is installed

@REM Create .env file (with the format as .env.example) in Backend to fill in the API key 
copy ".env-config\.env.example" "Backend\.env"

@REM Setup virtual environment (.venv)
CALL python -m venv .venv

@REM Activate the virtual environment (venv). 
CALL .\.venv\Scripts\activate.bat

@REM Install defined package for virtual environment
CALL pip install -r .env-config\requirements.txt

@REM Shut down the virtual environment
CALL .\.venv\Scripts\deactivate.bat

@REM Add instruction to fill in the API key in backend folder
echo.
echo.
echo.
echo !!! Remember to fill in the Groq API key in "backend/.env"