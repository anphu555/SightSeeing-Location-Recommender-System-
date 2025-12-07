import sys
import os
import pandas as pd

# Thêm thư mục gốc của dự án vào sys.path
# Điều này giúp Python tìm thấy các module trong 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.routers.recsysmodel import recommend_two_tower, load_resources

def run_test():
    """
    Hàm kiểm tra mô hình Two-Tower.
    """
    print("Bắt đầu kiểm tra mô hình Two-Tower...")

    # 1. Load tài nguyên (model, vocab, data)
    try:
        print("Đang tải tài nguyên...")
        load_resources()
        print("Tải tài nguyên thành công!")
    except Exception as e:
        print(f"LỖI: Không thể tải tài nguyên. Vui lòng kiểm tra lại đường dẫn file.")
        print(f"Chi tiết lỗi: {e}")
        return

    # 2. Định nghĩa các trường hợp kiểm tra
    # Test với cả viết hoa và viết thường để kiểm tra tính năng chuẩn hóa
    test_cases = {
        "Biển và thư giãn (viết hoa chuẩn)": ['Beach', 'Relaxing'],
        "Biển và thư giãn (viết thường)": ['beach', 'relaxing'],
        "Khám phá lịch sử (viết thường)": ['historical', 'cultural'],
        "Leo núi và thiên nhiên (mixed case)": ['MOUNTAIN', 'nature', 'TrEkKiNg'],
        "Ẩm thực địa phương (multi-word tags)": ['local cuisine', 'seafood'],
        "Tâm linh và chùa chiền": ['Religious', 'Pagoda', 'Temple'],
        "Không có sở thích (trường hợp cold start)": [],
    }

    # 3. Chạy kiểm tra
    for description, tags in test_cases.items():
        print("\n" + "="*50)
        print(f"Trường hợp kiểm tra: {description}")
        print(f"Tags đầu vào: {tags}")
        
        try:
            # Gọi hàm gợi ý
            recommendations = recommend_two_tower(tags, top_k=5)
            
            # In kết quả
            if not recommendations.empty:
                print(">>> Gợi ý hàng đầu:")
                # In kết quả với các cột quan trọng
                print(recommendations[['name', 'tags', 'score']].to_string(index=False))
            else:
                print(">>> Không tìm thấy gợi ý nào.")

        except Exception as e:
            print(f"LỖI khi chạy gợi ý cho tags {tags}: {e}")

    print("\n" + "="*50)
    print("Kiểm tra hoàn tất!")

if __name__ == "__main__":
    run_test()
