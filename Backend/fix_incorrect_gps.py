"""
Re-update GPS coordinates for places that have incorrect coordinates
Uses Google Geocoding API for maximum accuracy

Requirements:
    pip install googlemaps

Usage:
    python fix_incorrect_gps.py YOUR_API_KEY [start_id] [limit]
    
Example:
    python fix_incorrect_gps.py AIzaSyXXXXXXXXXXXXXX      # Fix all
    python fix_incorrect_gps.py AIzaSyXXXXXXXXXXXXXX 1 50 # Fix first 50
"""

import sqlite3
import sys
import time
import os
import json
from typing import Optional, Tuple
import googlemaps

def get_gps_from_google(gmaps_client, place_name: str, province: str = None) -> Optional[Tuple[float, float]]:
    """Get accurate GPS from Google Geocoding API"""
    try:
        if province:
            query = f"{place_name}, {province}, Vietnam"
        else:
            query = f"{place_name}, Vietnam"
        
        result = gmaps_client.geocode(query)
        
        if result and len(result) > 0:
            location = result[0]['geometry']['location']
            lat = location['lat']
            lon = location['lng']
            
            # Validate in Vietnam
            if 8.0 <= lat <= 24.0 and 102.0 <= lon <= 110.0:
                return (lat, lon)
        
        return None
            
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return None

def fix_incorrect_gps(api_key: str, start_from: int = 1, limit: Optional[int] = None):
    """Re-update GPS for places (including those with existing coordinates)"""
    
    db_path = "vietnamtravel.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize Google Maps client
    try:
        gmaps = googlemaps.Client(key=api_key)
        print("✅ Google Maps API connected\n")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Get ALL places (including those with GPS)
    if limit:
        cursor.execute("""
            SELECT id, name, tags, latitude, longitude
            FROM place 
            WHERE id >= ?
            ORDER BY id
            LIMIT ?
        """, (start_from, limit))
    else:
        cursor.execute("""
            SELECT id, name, tags, latitude, longitude
            FROM place 
            WHERE id >= ?
            ORDER BY id
        """, (start_from,))
    
    places = cursor.fetchall()
    total = len(places)
    
    print(f"📍 Updating GPS for {total} places...")
    print(f"   Estimated time: ~{total * 0.15 / 60:.1f} minutes\n")
    
    updated = 0
    failed = 0
    unchanged = 0
    
    start_time = time.time()
    
    for idx, (place_id, name, tags_json, old_lat, old_lon) in enumerate(places, 1):
        print(f"[{idx}/{total}] 🔍 ID {place_id}: {name[:50]}")
        
        # Parse tags for province
        province = None
        if tags_json:
            try:
                tags = json.loads(tags_json)
                if isinstance(tags, list) and len(tags) > 0:
                    province = tags[0]
            except:
                pass
        
        # Get new GPS
        gps = get_gps_from_google(gmaps, name, province)
        
        if gps:
            new_lat, new_lon = gps
            
            # Check if changed significantly (>0.01° = ~1km)
            if old_lat is None or old_lon is None:
                change = "NEW"
                changed = True
            else:
                lat_diff = abs(new_lat - old_lat)
                lon_diff = abs(new_lon - old_lon)
                if lat_diff > 0.01 or lon_diff > 0.01:
                    change = f"CHANGED ({lat_diff:.3f}°, {lon_diff:.3f}°)"
                    changed = True
                else:
                    change = "SAME"
                    changed = False
            
            if changed:
                cursor.execute("""
                    UPDATE place 
                    SET latitude = ?, longitude = ?
                    WHERE id = ?
                """, (new_lat, new_lon, place_id))
                conn.commit()
                
                print(f"  ✅ {change}: {new_lat:.6f}, {new_lon:.6f}")
                if old_lat and old_lon:
                    print(f"     Old: {old_lat:.6f}, {old_lon:.6f}")
                updated += 1
            else:
                print(f"  ✓ Already accurate")
                unchanged += 1
        else:
            print(f"  ❌ Not found")
            failed += 1
        
        time.sleep(0.1)  # Rate limit
        
        if idx % 50 == 0:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = (total - idx) / rate if rate > 0 else 0
            
            print(f"\n--- Progress: {idx}/{total} ({idx/total*100:.1f}%) ---")
            print(f"    ✅ Updated: {updated} | ✓ Unchanged: {unchanged} | ❌ Failed: {failed}")
            print(f"    ⏱️  Remaining: ~{remaining/60:.1f} min\n")
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print("🎉 GPS Fix Complete!")
    print("="*70)
    print(f"✅ Updated:   {updated}")
    print(f"✓  Unchanged: {unchanged}")
    print(f"❌ Failed:    {failed}")
    print(f"⏱️  Time:     {elapsed/60:.1f} min")
    print(f"📈 Success:   {(updated+unchanged)/total*100 if total > 0 else 0:.1f}%")
    print("="*70)
    
    conn.close()

if __name__ == "__main__":
    print("="*70)
    print("📍 GPS Accuracy Fixer (Google Geocoding)")
    print("="*70)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python fix_incorrect_gps.py YOUR_API_KEY [start_id] [limit]")
        print("\nExamples:")
        print("  python fix_incorrect_gps.py AIzaSyXXXXXXXXXXXXXX")
        print("  python fix_incorrect_gps.py AIzaSyXXXXXXXXXXXXXX 1 100")
        print("\nGet API Key:")
        print("  1. https://console.cloud.google.com/")
        print("  2. Enable 'Geocoding API'")
        print("  3. Create API Key")
        print("="*70)
        sys.exit(1)
    
    api_key = sys.argv[1]
    start_from = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if limit:
        print(f"\n📝 Will update {limit} places starting from ID {start_from}")
    else:
        print(f"\n📝 Will update ALL places starting from ID {start_from}")
    
    print("\n⚠️  This uses Google Geocoding API")
    print("   Cost: ~$5 per 1000 places")
    print("   Free tier: $200/month (~40,000 requests)")
    print("="*70)
    
    input("\nPress Enter to start, or Ctrl+C to cancel...")
    print("="*70 + "\n")
    
    fix_incorrect_gps(api_key, start_from, limit)
