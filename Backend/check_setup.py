"""
SETUP SCRIPT - Kiểm tra và cài đặt dependencies
"""

import subprocess
import sys

def check_and_install():
    """Kiểm tra và cài đặt các packages cần thiết"""
    
    required_packages = [
        'pandas',
        'numpy',
        'scikit-learn',
        'sqlmodel',
        'fastapi'
    ]
    
    print("="*70)
    print("KIỂM TRA DEPENDENCIES")
    print("="*70)
    print()
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} - OK")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Thiếu {len(missing)} packages: {', '.join(missing)}")
        print("\n💡 Để cài đặt, chạy:")
        print(f"   pip install -r requirements.txt")
        print("\nHoặc cài từng package:")
        for pkg in missing:
            print(f"   pip install {pkg}")
        return False
    else:
        print("\n✅ Tất cả dependencies đã được cài đặt!")
        return True

if __name__ == "__main__":
    success = check_and_install()
    
    if success:
        print("\n" + "="*70)
        print("SẴN SÀNG CHẠY EVALUATION!")
        print("="*70)
        print("\nNext steps:")
        print("1. python quick_demo.py          - Chạy demo nhanh")
        print("2. python create_test_data.py    - Tạo test data")
        print("3. python evaluate_recsys.py     - Chạy full evaluation")
    else:
        print("\n❌ Vui lòng cài đặt dependencies trước")
        sys.exit(1)
