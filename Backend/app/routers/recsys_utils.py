from sqlmodel import Session, select
from app.schemas import Rating, Place, InteractionType
from collections import Counter

def build_profile_from_history(user_id: int, session: Session, limit_tags=10):
    """
    Tự động tạo list tags sở thích dựa trên lịch sử tương tác của user.
    """
    # 1. Lấy các địa điểm user đã tương tác tích cực
    # (Ví dụ: like, click, view hoặc score cao)
    statement = select(Rating).where(
        Rating.user_id == user_id,
        Rating.score >= 3.0  # Chỉ lấy những nơi user đánh giá tốt hoặc quan tâm
    )
    ratings = session.exec(statement).all()
    
    if not ratings:
        return []

    # 2. Tổng hợp tất cả tags từ các địa điểm đó
    all_tags = []
    for rating in ratings:
        # rating.place có thể chưa được load (lazy loading), nên query place nếu cần
        # Ở đây giả sử relationship đã hoạt động hoặc query join
        place = session.get(Place, rating.place_id) 
        if place and place.tags:
            # place.tags là list (do schema định nghĩa JSON)
            all_tags.extend(place.tags)
            
    # 3. (Nâng cao) Lấy ra các tags xuất hiện nhiều nhất
    # Ví dụ: User like 5 chỗ "Biển", 1 chỗ "Núi" -> Ưu tiên "Biển"
    if not all_tags:
        return []
        
    tag_counts = Counter(all_tags)
    # Lấy top N tags phổ biến nhất trong lịch sử user
    top_tags = [tag for tag, count in tag_counts.most_common(limit_tags)]
    
    return top_tags