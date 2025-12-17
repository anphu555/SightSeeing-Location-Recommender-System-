#!/bin/bash
# Chạy full evaluation với venv

cd "$(dirname "$0")"
source ../.venv/bin/activate
python evaluate_recsys.py
