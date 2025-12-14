# 📍 GPS-Based Location Sorting Feature

## Tổng quan

Hệ thống đã được tích hợp tính năng **sắp xếp địa điểm theo khoảng cách GPS**, cho phép người dùng tìm kiếm các địa điểm du lịch gần vị trí hiện tại của họ.

## ✨ Tính năng chính

### 1. **Lấy vị trí GPS của người dùng**
- Tự động request quyền truy cập vị trí từ trình duyệt
- Cache vị trí trong 5 phút để tiết kiệm battery
- Hỗ trợ high-accuracy GPS positioning

### 2. **Tính toán khoảng cách**
- Sử dụng công thức **Haversine** để tính khoảng cách chính xác
- Hiển thị khoảng cách (km) trên mỗi card địa điểm
- Sắp xếp từ gần đến xa

### 3. **UI/UX**
- Thêm option **"Near Me"** trong dropdown sort
- Badge đỏ hiển thị khoảng cách ở góc dưới bên trái của ảnh
- Loading state khi đang lấy GPS

## 📊 Dữ liệu hiện tại

- **Total places:** 928
- **Places with GPS:** 666 (71.8%)
- **Coverage provinces:** 63+ tỉnh/thành phố

## 🔧 Cách sử dụng

### Cho người dùng (Frontend)

1. Vào trang **Results** (`results.html`)
2. Click vào dropdown **"Sort by"**
3. Chọn **"Near Me"** (icon location)
4. Cho phép trình duyệt truy cập vị trí khi được yêu cầu
5. Hệ thống sẽ hiển thị các địa điểm gần nhất

### Cho developer

#### Backend API

**Endpoint:** `GET /api/v1/place/search/nearby`

**Parameters:**
- `lat` (required): Latitude của user
- `lon` (required): Longitude của user  
- `limit` (optional, default=50): Số lượng kết quả
- `max_distance` (optional, default=500): Bán kính tìm kiếm (km)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Temple of Literature",
    "description": [...],
    "image": [...],
    "tags": ["Ha Noi", "Historical"],
    "province": "Ha Noi",
    "distance": 2.5,
    "latitude": 21.0277,
    "longitude": 105.8355
  }
]
```

#### Frontend Usage

```javascript
import { getUserLocationWithCache, formatDistance } from './gps-utils.js';

// Lấy vị trí user
const userCoords = await getUserLocationWithCache();

// Gọi API
const response = await fetch(
  `${CONFIG.apiBase}/api/v1/place/search/nearby?lat=${userCoords.lat}&lon=${userCoords.lon}&limit=50`
);

const places = await response.json();

// Format distance
const distanceText = formatDistance(places[0].distance); // "2.5 km"
```

## 📁 Files đã thay đổi

### Backend
- ✅ `Backend/app/schemas.py` - Thêm latitude/longitude vào Place model
- ✅ `Backend/app/routers/place.py` - API endpoint nearby search + haversine
- ✅ `Backend/alembic/versions/7810123c6d98_*.py` - Migration file
- ✅ `Backend/bulk_update_gps.py` - Script update GPS data
- ✅ `Backend/update_gps_data.py` - Script update GPS (deprecated)

### Frontend
- ✅ `frontend/exSighting/src/js/gps-utils.js` - GPS utilities (NEW)
- ✅ `frontend/exSighting/src/js/result.js` - Sort by distance logic
- ✅ `frontend/exSighting/src/css/style.css` - Distance badge styling
- ✅ `frontend/exSighting/results.html` - Near Me option trong dropdown

## 🛠️ Setup & Update GPS Data

### 1. Run migration (đã chạy rồi)
```bash
cd Backend
alembic upgrade head
```

### 2. Update GPS data cho places
```bash
cd Backend
python bulk_update_gps.py
# Nhập 'yes' để confirm
```

### 3. Restart backend server
```bash
cd Backend
uvicorn app.main:app --reload
```

## 🔮 Tính năng tương lai

### Phase 2: Enhanced GPS Features
- [ ] **Distance Filter Slider**: Cho user chọn bán kính tìm kiếm (10km, 50km, 100km, 500km)
- [ ] **Map View**: Hiển thị places trên bản đồ (Google Maps/Leaflet)
- [ ] **Direction Button**: Link đến Google Maps directions
- [ ] **Current Location Marker**: Hiển thị vị trí user trên map

### Phase 3: Advanced Features
- [ ] **Route Planning**: Suggest optimal route visiting multiple places
- [ ] **Nearby Places on Detail Page**: "Places nearby this location"
- [ ] **GPS-based Recommendations**: Ưu tiên recommend places gần user
- [ ] **Travel Time Estimation**: Ước tính thời gian di chuyển (car/bike/walk)

### Phase 4: Data Enhancement
- [ ] **Auto GPS Lookup**: Tự động lấy GPS từ Google Places API
- [ ] **User GPS Contribution**: Cho phép user update/correct GPS
- [ ] **Place Clustering**: Group places gần nhau thành cluster
- [ ] **Coverage Analytics**: Dashboard hiển thị coverage by province

## 🐛 Known Issues

1. **Permission Denied**: User từ chối GPS → Show fallback message
2. **Low Coverage**: 28.2% places chưa có GPS → Cần update thêm data
3. **Cache Issues**: Cache 5 phút có thể outdated nếu user di chuyển xa
4. **Performance**: Haversine calculation on 666 places ~ 50-100ms

## 📝 Notes

- GPS coordinates được tính dựa trên **tỉnh/thành phố** với random offset nhỏ (±0.1 độ ~ ±11km)
- Với các địa điểm nổi tiếng, nên update GPS chính xác hơn thủ công
- Trình duyệt **phải hỗ trợ Geolocation API** (Chrome, Firefox, Safari, Edge modern)
- **HTTPS required** cho production (HTTP chỉ work trên localhost)

## 🎯 Testing Checklist

- [x] Backend API `/api/v1/place/search/nearby` works
- [x] GPS data populated in database (666/928 places)
- [x] Frontend "Near Me" option appears in dropdown
- [x] Permission request shows up
- [x] Distance badge displays correctly
- [x] Results sorted by distance (nearest first)
- [ ] Test on mobile devices
- [ ] Test with location services disabled
- [ ] Test with different distances
- [ ] Performance test with 900+ places

---

**Developed by:** [Your Team]  
**Date:** December 14, 2025  
**Version:** 1.0.0
