#!/usr/bin/env python3
"""
Fix incorrect GPS coordinates for Vietnamese tourist destinations
Based on analysis of database and manual verification from Google Maps
"""

import sqlite3
import sys

# Accurate GPS coordinates verified from Google Maps
GPS_CORRECTIONS = {
    # ID 522: Cat Ba National Park - CORRECT (it's in Quang Ninh, near Haiphong ~lat 20-21)
    # Current: 21.044497, 107.161124 - This is actually correct for Cat Ba
    
    # ID 102: Da Lat Market
    # Current: 11.566832, 108.175452 - WRONG
    # Correct: Dalat Market (Cho Da Lat) is in center of Dalat city
    102: (11.940419, 108.438262, "Da Lat Market - Cho Da Lat, city center"),
    
    # ID 775: Ho Chi Minh Museum in Thua Thien Hue
    # Current: 10.766895, 106.691532 - WRONG (this is HCMC coordinates!)
    # Correct: Ho Chi Minh Museum in Hue
    775: (16.467430, 107.578735, "Ho Chi Minh Museum - Hue city, near Perfume River"),
    
    # ID 73: Hoi An City
    # Current: 15.446558, 108.008406 - WRONG (too far south)
    # Correct: Hoi An Ancient Town center
    73: (15.879778, 108.335002, "Hoi An Ancient Town - city center"),
    
    # ID 315: Nguyen Hue Walking Street
    # Current: 10.831787, 106.617045 - seems off
    # Correct: Nguyen Hue Walking Street in HCMC (from Saigon River to City Hall)
    315: (10.774171, 106.701008, "Nguyen Hue Walking Street - HCMC, District 1"),
    
    # ID 410: Vinpearl Safari Phu Quoc - CORRECT
    # Current: 10.034213, 105.129639 - This is correct for Phu Quoc Island
    # (Phu Quoc is in the south, lat ~10)
    
    # Additional corrections based on common knowledge
    # Let me check for more potential issues...
}

def fix_coordinates():
    """Update GPS coordinates in the database"""
    conn = sqlite3.connect('vietnamtravel.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("GPS COORDINATES CORRECTION TOOL")
    print("=" * 80)
    print()
    
    updated_count = 0
    
    for place_id, (lat, lon, description) in GPS_CORRECTIONS.items():
        # Get current coordinates
        cursor.execute(
            "SELECT name, latitude, longitude FROM place WHERE id = ?",
            (place_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            print(f"⚠️  Place ID {place_id} not found in database")
            continue
        
        name, old_lat, old_lon = result
        
        # Calculate distance difference (rough estimate)
        lat_diff = abs(lat - (old_lat or 0))
        lon_diff = abs(lon - (old_lon or 0))
        distance_km = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111  # ~111km per degree
        
        print(f"📍 ID {place_id}: {name}")
        print(f"   Description: {description}")
        if old_lat and old_lon:
            print(f"   Old GPS: {old_lat:.6f}, {old_lon:.6f}")
            print(f"   New GPS: {lat:.6f}, {lon:.6f}")
            print(f"   Distance correction: ~{distance_km:.1f}km")
        else:
            print(f"   Old GPS: None")
            print(f"   New GPS: {lat:.6f}, {lon:.6f}")
        
        # Update coordinates
        cursor.execute(
            "UPDATE place SET latitude = ?, longitude = ? WHERE id = ?",
            (lat, lon, place_id)
        )
        
        if cursor.rowcount > 0:
            print(f"   ✅ Updated successfully")
            updated_count += 1
        else:
            print(f"   ❌ Update failed")
        print()
    
    conn.commit()
    
    # Get final GPS coverage statistics
    cursor.execute("SELECT COUNT(*) FROM place")
    total_places = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM place WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    places_with_gps = cursor.fetchone()[0]
    
    coverage_pct = (places_with_gps / total_places * 100) if total_places > 0 else 0
    
    print("=" * 80)
    print(f"✅ Successfully updated {updated_count} place(s)")
    print(f"📊 Database GPS coverage: {places_with_gps}/{total_places} ({coverage_pct:.1f}%)")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    try:
        fix_coordinates()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
