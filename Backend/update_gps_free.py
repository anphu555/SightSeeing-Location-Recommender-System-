"""
Update GPS coordinates using FREE Nominatim API (OpenStreetMap)
NO API KEY REQUIRED - Completely FREE!

Requirements:
    pip install geopy

Usage:
    python update_gps_free.py [start_id] [limit]
"""

import sqlite3
import sys
import time
import os
import json
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def get_gps_from_nominatim(geolocator, place_name: str, province: str = None) -> Optional[Tuple[float, float]]:
    """Get GPS coordinates from Nominatim"""
    try:
        if province:
            query = f"{place_name}, {province}, Vietnam"
        else:
            query = f"{place_name}, Vietnam"
        
        location = geolocator.geocode(query, timeout=10)
        
        if location:
            lat = location.latitude
            lon = location.longitude
            
            # Validate in Vietnam
            if 8.0 <= lat <= 24.0 and 102.0 <= lon <= 110.0:
                return (lat, lon)
        
        return None
            
    except (GeocoderTimedOut, GeocoderServiceError):
        return None
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return None

def update_all_gps_free(start_from: int = 0, limit: Optional[int] = None):
    """Update GPS for all places using FREE Nominatim API"""
    
    db_path = "vietnamtravel.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize Nominatim
    geolocator = Nominatim(user_agent="vietnam_tourism_app_v1.0")
    print("✅ Nominatim API connected (OpenStreetMap)\n")
    
    # Get places without GPS
    if limit:
        cursor.execute("""
            SELECT id, name, tags
            FROM place 
            WHERE id >= ? AND (latitude IS NULL OR longitude IS NULL)
            ORDER BY id
            LIMIT ?
        """, (start_from, limit))
    else:
        cursor.execute("""
            SELECT id, name, tags
            FROM place 
            WHERE id >= ? AND (latitude IS NULL OR longitude IS NULL)
            ORDER BY id
        """, (start_from,))
    
    places = cursor.fetchall()
    total = len(places)
    
    if total == 0:
        print("✅ All places already have GPS coordinates!")
        return
    
    print(f"📍 Starting GPS update for {total} places...")
    print(f"   Estimated time: ~{total * 2 / 60:.1f} minutes\n")
    
    updated = 0
    failed = 0
    
    start_time = time.time()
    
    for idx, (place_id, name, tags_json) in enumerate(places, 1):
        print(f"[{idx}/{total}] 🔍 ID {place_id}: {name[:50]}")
        
        # Parse tags for province hint
        province = None
        if tags_json:
            try:
                tags = json.loads(tags_json)
                if isinstance(tags, list) and len(tags) > 0:
                    province = tags[0]
            except:
                pass
        
        # Get GPS
        gps = get_gps_from_nominatim(geolocator, name, province)
        
        if gps is None:
            print(f"  🔄 Retrying...")
            time.sleep(2)
            gps = get_gps_from_nominatim(geolocator, name, province)
        
        if gps:
            lat, lon = gps
            cursor.execute("""
                UPDATE place 
                SET latitude = ?, longitude = ?
                WHERE id = ?
            """, (lat, lon, place_id))
            conn.commit()
            
            print(f"  ✅ Updated: {lat:.6f}, {lon:.6f}")
            updated += 1
        else:
            print(f"  ❌ Not found")
            failed += 1
        
        time.sleep(1.5)  # Rate limit
        
        if idx % 20 == 0:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = (total - idx) / rate if rate > 0 else 0
            
            print(f"\n--- Progress: {idx}/{total} ({idx/total*100:.1f}%) ---")
            print(f"    ✅ Updated: {updated} | ❌ Failed: {failed}")
            print(f"    ⏱️  Remaining: ~{remaining/60:.1f} min\n")
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print("🎉 GPS Update Complete!")
    print("="*70)
    print(f"✅ Updated: {updated}")
    print(f"❌ Failed:  {failed}")
    print(f"⏱️  Time:   {elapsed/60:.1f} min")
    print(f"📈 Success: {updated/total*100 if total > 0 else 0:.1f}%")
    print("="*70)
    
    # Show coverage
    cursor.execute("SELECT COUNT(*) FROM place WHERE latitude IS NOT NULL")
    total_with_gps = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM place")
    total_places = cursor.fetchone()[0]
    
    print(f"\n📊 Database Coverage: {total_with_gps}/{total_places} ({total_with_gps/total_places*100:.1f}%)")
    
    conn.close()

if __name__ == "__main__":
    print("="*70)
    print("📍 FREE GPS Updater (Nominatim/OpenStreetMap)")
    print("="*70)
    
    start_from = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if limit:
        print(f"\n📝 Will update {limit} places starting from ID {start_from}")
    else:
        print(f"\n📝 Will update ALL places without GPS starting from ID {start_from}")
    
    print("\n⚠️  This uses FREE OpenStreetMap API")
    print("   Rate limit: 1 request per 1.5 seconds")
    print("   Success rate: ~40-60% for Vietnamese place names")
    print("="*70)
    
    input("\nPress Enter to start, or Ctrl+C to cancel...")
    print("="*70 + "\n")
    
    update_all_gps_free(start_from, limit)
