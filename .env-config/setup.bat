@echo off
@REM Create .env file (with the format as .env.example) in Backend to fill in the API key 
copy ".env-config\.env.example" "Backend\.env"

CALL python -m venv .venv

@REM REM Activate the virtual environment (venv). 
CALL .\.venv\Scripts\activate.bat

CALL pip install -r .env-config\requirements.txt

CALL .\.venv\Scripts\deactivate.bat
