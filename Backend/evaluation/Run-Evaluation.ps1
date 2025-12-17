#!/usr/bin/env pwsh
# PowerShell script để chạy evaluation với venv

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "CHẠY EVALUATION VỚI VENV" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
Set-Location "D:\SightSeeing-Location-Recommender-System-"

# Activate venv
Write-Host "⏳ Activating venv..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check activation
if ($VIRTUAL_ENV) {
    Write-Host "✓ Venv activated: $VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to activate venv" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Change to backend
Set-Location backend

# Run quick demo
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "1. QUICK DEMO" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
python quick_demo.py

# Ask to continue
Write-Host ""
Write-Host "Nhấn Enter để tạo test data (hoặc Ctrl+C để dừng)..." -ForegroundColor Yellow
Read-Host

# Create test data
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "2. TẠO TEST DATA" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
python create_test_data.py

# Ask to continue
Write-Host ""
Write-Host "Nhấn Enter để chạy full evaluation (hoặc Ctrl+C để dừng)..." -ForegroundColor Yellow
Read-Host

# Run evaluation
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "3. FULL EVALUATION" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
python evaluate_recsys.py

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "✅ HOÀN TẤT!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Kết quả đã được lưu tại:" -ForegroundColor Yellow
Write-Host "   - evaluation_results.json"
Write-Host "   - evaluation_detailed.csv"
