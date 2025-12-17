#!/bin/bash
# Tạo test data với venv

cd "$(dirname "$0")"
source ../.venv/bin/activate
python create_test_data.py
