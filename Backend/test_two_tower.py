"""
Test script for Two-Tower model implementation
"""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("Testing Two-Tower Model Implementation")
print("=" * 60)

# Test 1: Import modules
print("\n[Test 1] Importing modules...")
try:
    from app.routers import recsysmodel
    print("✓ Successfully imported recsysmodel")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Check functions exist
print("\n[Test 2] Checking functions...")
required_functions = [
    'initialize_recsys',
    'recommend_two_tower_deep',
    'recommend_two_tower',
    'recommend_content_based',
    'recommend',
    'load_two_tower_model',
    'load_item_embeddings',
    'load_province_dictionary'
]

for func_name in required_functions:
    if hasattr(recsysmodel, func_name):
        print(f"  ✓ {func_name} exists")
    else:
        print(f"  ✗ {func_name} not found")

# Test 3: Check model files
print("\n[Test 3] Checking model files...")
from pathlib import Path
model_dir = Path("app/routers")
required_files = [
    'two_tower_model.h5',
    'item_embeddings.pkl',
    'province_dictionary.pkl',
    'places_metadata.csv'
]

for file_name in required_files:
    file_path = model_dir / file_name
    if file_path.exists():
        print(f"  ✓ {file_name} found")
    else:
        print(f"  ✗ {file_name} not found")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
