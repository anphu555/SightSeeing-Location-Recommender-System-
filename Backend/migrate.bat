@echo off
REM Script to create and apply database migrations using Alembic

echo ================================
echo   Alembic Migration Tool
echo ================================
echo.

if "%1"=="" (
    echo Usage:
    echo   migrate.bat create [message]  - Create a new migration
    echo   migrate.bat upgrade           - Apply all pending migrations
    echo   migrate.bat downgrade         - Rollback one migration
    echo   migrate.bat current           - Show current revision
    echo   migrate.bat history           - Show migration history
    echo.
    goto :end
)

cd /d %~dp0

if "%1"=="create" (
    if "%2"=="" (
        echo Error: Please provide a message for the migration
        echo Example: migrate.bat create "Add email field to User"
        goto :end
    )
    echo Creating new migration: %2
    python -m alembic revision --autogenerate -m "%~2"
    echo.
    echo Migration created! Review the file in alembic/versions/
    echo To apply it, run: migrate.bat upgrade
    goto :end
)

if "%1"=="upgrade" (
    echo Applying migrations...
    python -m alembic upgrade head
    echo Done!
    goto :end
)

if "%1"=="downgrade" (
    echo Rolling back last migration...
    python -m alembic downgrade -1
    echo Done!
    goto :end
)

if "%1"=="current" (
    python -m alembic current
    goto :end
)

if "%1"=="history" (
    python -m alembic history
    goto :end
)

echo Unknown command: %1
echo Run migrate.bat without arguments to see usage

:end
