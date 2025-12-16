/**
 * GPS Utilities - Các hàm tiện ích cho việc xử lý vị trí địa lý
 */

// Cache thời gian lưu vị trí (5 phút)
const LOCATION_CACHE_DURATION = 5 * 60 * 1000;
let cachedLocation = null;
let cacheTimestamp = null;

/**
 * Kiểm tra trình duyệt có hỗ trợ Geolocation không
 */
export function isGeolocationSupported() {
    return 'geolocation' in navigator;
}

/**
 * Lấy vị trí người dùng với cache
 * @returns {Promise<{lat: number, lon: number}>}
 */
export async function getUserLocationWithCache() {
    // Kiểm tra cache còn hiệu lực không
    if (cachedLocation && cacheTimestamp) {
        const now = Date.now();
        if (now - cacheTimestamp < LOCATION_CACHE_DURATION) {
            return cachedLocation;
        }
    }
    
    // Lấy vị trí mới
    const location = await getUserLocation();
    
    // Lưu cache
    cachedLocation = location;
    cacheTimestamp = Date.now();
    
    return location;
}

/**
 * Lấy vị trí người dùng từ Geolocation API
 * @returns {Promise<{lat: number, lon: number}>}
 */
export function getUserLocation() {
    return new Promise((resolve, reject) => {
        if (!isGeolocationSupported()) {
            reject(new Error('Geolocation is not supported by this browser'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                });
            },
            (error) => {
                let message = 'Unknown error';
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        message = 'User denied the request for Geolocation';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message = 'Location information is unavailable';
                        break;
                    case error.TIMEOUT:
                        message = 'The request to get user location timed out';
                        break;
                }
                reject(new Error(message));
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: LOCATION_CACHE_DURATION
            }
        );
    });
}

/**
 * Tính khoảng cách giữa 2 điểm (Haversine formula)
 * @param {number} lat1 - Vĩ độ điểm 1
 * @param {number} lon1 - Kinh độ điểm 1
 * @param {number} lat2 - Vĩ độ điểm 2
 * @param {number} lon2 - Kinh độ điểm 2
 * @returns {number} Khoảng cách tính bằng km
 */
export function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Bán kính Trái Đất (km)
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    
    return R * c;
}

/**
 * Chuyển đổi độ sang radian
 */
function toRad(deg) {
    return deg * (Math.PI / 180);
}

/**
 * Format khoảng cách để hiển thị
 * @param {number} distanceKm - Khoảng cách (km)
 * @returns {string} Chuỗi đã format
 */
export function formatDistance(distanceKm) {
    if (distanceKm < 1) {
        return `${Math.round(distanceKm * 1000)} m`;
    } else if (distanceKm < 10) {
        return `${distanceKm.toFixed(1)} km`;
    } else {
        return `${Math.round(distanceKm)} km`;
    }
}

/**
 * Xóa cache vị trí
 */
export function clearLocationCache() {
    cachedLocation = null;
    cacheTimestamp = null;
}
