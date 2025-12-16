import time
from app.routers.recsysmodel import (
    load_places_from_db,
    recommend_two_tower,
    recommend_two_tower_tfidf,
)


def main():
    # 1. Load dữ liệu thật
    print("--- Loading Data ---")
    df = load_places_from_db()
    if df.empty:
        print("Không có dữ liệu để test")
        return

    # Lấy query tags từ địa điểm đầu tiên (giả lập intent của user)
    first_tags = df.iloc[0]["tags"]
    if not first_tags:
        print("Bản ghi đầu tiên không có tags, dùng fallback ['nature']")
        query_tags = ["nature"]
    else:
        query_tags = first_tags

    print(f"Query tags dùng cho benchmark: {query_tags}")

    user_id = None  # Có thể set user_id cụ thể nếu muốn test với history
    top_k = 10

    # 2. Benchmark CountVectorizer-based model
    start_cv = time.time()
    results_cv = recommend_two_tower(query_tags, user_id=user_id, top_k=top_k)
    end_cv = time.time()
    time_cv = end_cv - start_cv

    # 3. Benchmark TF-IDF-based model
    start_tfidf = time.time()
    results_tfidf = recommend_two_tower_tfidf(query_tags, user_id=user_id, top_k=top_k)
    end_tfidf = time.time()
    time_tfidf = end_tfidf - start_tfidf

    # 4. In kết quả
    print("\n--- KẾT QUẢ BENCHMARK (END-TO-END PIPELINE) ---")
    print(f"CountVectorizer model time: {time_cv:.4f} seconds")
    print(f"TF-IDF model time        : {time_tfidf:.4f} seconds")

    def print_top(df_results, title):
        print(f"\n{title}")
        if df_results is None or df_results.empty:
            print("  (Không có kết quả)")
            return
        for _, row in df_results.head(5).iterrows():
            place_id = row.get("id", "N/A")
            tags = row.get("tags", "N/A")
            print(
                f" - ID: {place_id} | Name: {row['name']} | "
                f"Score: {row['score']:.4f} | Tags: {tags}"
            )

    print_top(results_cv, "TOP 5 CountVectorizer Recommendations:")
    print_top(results_tfidf, "TOP 5 TF-IDF Recommendations:")

    # 5. Phân tích overlap giữa 2 mô hình
    if not results_cv.empty and not results_tfidf.empty:
        set_cv = set(results_cv["id"].tolist())
        set_tfidf = set(results_tfidf["id"].tolist())
        overlap = set_cv & set_tfidf
        print(f"\nSố lượng địa điểm trùng nhau trong TOP {top_k}: {len(overlap)}")
        if overlap:
            print("IDs trùng nhau:", list(overlap))


if __name__ == "__main__":
    main()