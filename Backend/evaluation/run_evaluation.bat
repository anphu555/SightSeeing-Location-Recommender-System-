@echo off
REM Batch script để chạy evaluation qua WSL

echo ======================================================================
echo CHẠY EVALUATION TRONG WSL
echo ======================================================================
echo.

echo Dang chay Quick Demo...
echo.
wsl bash -c "cd /mnt/d/SightSeeing-Location-Recommender-System-/backend && source ../.venv/bin/activate && python quick_demo.py"

echo.
echo.
pause
echo.

echo Dang tao Test Data...
echo.
wsl bash -c "cd /mnt/d/SightSeeing-Location-Recommender-System-/backend && source ../.venv/bin/activate && python create_test_data.py"

echo.
echo.
pause
echo.

echo Dang chay Full Evaluation...
echo.
wsl bash -c "cd /mnt/d/SightSeeing-Location-Recommender-System-/backend && source ../.venv/bin/activate && python evaluate_recsys.py"

echo.
echo ======================================================================
echo HOAN TAT!
echo ======================================================================
echo.
echo Ket qua da duoc luu tai:
echo    - evaluation_results.json
echo    - evaluation_detailed.csv
echo.
pause
