#!/bin/bash
# Script để chạy evaluation với venv trong WSL

echo "========================================================================"
echo "CHẠY EVALUATION VỚI VENV (WSL)"
echo "========================================================================"
echo ""

# Activate venv
echo "⏳ Activating venv..."
source ../.venv/bin/activate

# Check if activation worked
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate venv"
    exit 1
fi

echo "✓ Venv activated: $VIRTUAL_ENV"
echo ""

# Run quick demo
echo "========================================================================"
echo "1. QUICK DEMO"
echo "========================================================================"
python quick_demo.py

echo ""
read -p "Nhấn Enter để tiếp tục tạo test data..."

# Create test data
echo ""
echo "========================================================================"
echo "2. TẠO TEST DATA"
echo "========================================================================"
python create_test_data.py

echo ""
read -p "Nhấn Enter để chạy full evaluation..."

# Run full evaluation
echo ""
echo "========================================================================"
echo "3. FULL EVALUATION"
echo "========================================================================"
python evaluate_recsys.py

echo ""
echo "========================================================================"
echo "✅ HOÀN TẤT!"
echo "========================================================================"
echo ""
echo "📁 Kết quả đã được lưu tại:"
echo "   - evaluation_results.json"
echo "   - evaluation_detailed.csv"
