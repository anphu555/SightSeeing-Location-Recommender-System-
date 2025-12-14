// === GPS UTILITIES ===
// Module để xử lý các chức năng liên quan đến GPS/Geolocation

/**
 * Lấy vị trí GPS hiện tại của người dùng
 * @returns {Promise<{lat: number, lon: number}>}
 */
export function getUserLocation() {
    return new Promise((resolve, reject) => {
        // Check if browser supports Geolocation API
        if (!navigator.geolocation) {
            reject(new Error('Your browser does not support GPS location'));
            return;
        }
        
        console.log('🌍 Getting your location...');
        
        navigator.geolocation.getCurrentPosition(
            // Success callback
            (position) => {
                const coords = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                };
                console.log('✅ Your location:', coords);
                resolve(coords);
            },
            // Error callback
            (error) => {
                let errorMessage = 'Unable to get location';
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location access denied. Please enable location permission in your browser settings.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information unavailable';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out';
                        break;
                }
                
                console.error('❌ GPS Error:', errorMessage);
                reject(new Error(errorMessage));
            },
            // Options - Optimized for speed
            {
                enableHighAccuracy: false, // Use network location for faster response
                timeout: 5000,             // Reduced timeout to 5 seconds
                maximumAge: 60000          // Cache for 1 minute only
            }
        );
    });
}

/**
 * Kiểm tra xem trình duyệt có hỗ trợ Geolocation không
 * @returns {boolean}
 */
export function isGeolocationSupported() {
    return 'geolocation' in navigator;
}

/**
 * Yêu cầu quyền truy cập vị trí (nếu cần)
 * @returns {Promise<PermissionState>}
 */
export async function checkLocationPermission() {
    if (!navigator.permissions) {
        return 'prompt'; // Trình duyệt cũ không hỗ trợ Permissions API
    }
    
    try {
        const result = await navigator.permissions.query({ name: 'geolocation' });
        return result.state; // 'granted', 'denied', hoặc 'prompt'
    } catch (error) {
        console.warn('Không thể kiểm tra quyền vị trí:', error);
        return 'prompt';
    }
}

/**
 * Tính khoảng cách giữa 2 điểm GPS (Haversine formula)
 * @param {number} lat1 - Latitude điểm 1
 * @param {number} lon1 - Longitude điểm 1
 * @param {number} lat2 - Latitude điểm 2
 * @param {number} lon2 - Longitude điểm 2
 * @returns {number} Khoảng cách tính bằng km
 */
export function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Bán kính Trái Đất (km)
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    
    const a = 
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    return Math.round(distance * 100) / 100; // Làm tròn 2 chữ số thập phân
}

/**
 * Chuyển độ sang radian
 * @param {number} degrees 
 * @returns {number}
 */
function toRad(degrees) {
    return degrees * (Math.PI / 180);
}

/**
 * Format khoảng cách thành string dễ đọc
 * @param {number} km - Khoảng cách tính bằng km
 * @returns {string}
 */
export function formatDistance(km) {
    if (km < 1) {
        return `${Math.round(km * 1000)}m`;
    } else if (km < 10) {
        return `${km.toFixed(1)} km`;
    } else {
        return `${Math.round(km)} km`;
    }
}

/**
 * Lưu vị trí vào localStorage (để cache)
 * @param {{lat: number, lon: number}} coords 
 */
export function saveUserLocation(coords) {
    const data = {
        ...coords,
        timestamp: Date.now()
    };
    localStorage.setItem('userLocation', JSON.stringify(data));
}

/**
 * Lấy vị trí đã lưu từ localStorage
 * @param {number} maxAge - Thời gian cache tối đa (ms), mặc định 5 phút
 * @returns {{lat: number, lon: number} | null}
 */
export function getCachedLocation(maxAge = 300000) {
    try {
        const cached = localStorage.getItem('userLocation');
        if (!cached) return null;
        
        const data = JSON.parse(cached);
        const age = Date.now() - data.timestamp;
        
        if (age > maxAge) {
            localStorage.removeItem('userLocation');
            return null;
        }
        
        return { lat: data.lat, lon: data.lon };
    } catch (error) {
        console.error('Lỗi đọc cached location:', error);
        return null;
    }
}

/**
 * Lấy vị trí (ưu tiên cache, nếu hết hạn thì fetch mới)
 * @returns {Promise<{lat: number, lon: number}>}
 */
export async function getUserLocationWithCache() {
    const cached = getCachedLocation();
    if (cached) {
        console.log('📍 Using cached location:', cached);
        return cached;
    }
    
    const location = await getUserLocation();
    saveUserLocation(location);
    return location;
}
