#!/usr/bin/env python3
"""
Script to fix province tags in the place table.
Uses smart algorithmic approach focusing on explicit location mentions in descriptions.
"""

import sqlite3
import json
import os
import re

# Standard province names
STANDARD_PROVINCES = [
    "An Giang", "Ba Ria - Vung Tau", "Bac Giang", "Bac Kan", "Bac Lieu",
    "Bac Ninh", "Ben Tre", "Binh Dinh", "Binh Duong", "Binh Phuoc", "Binh Thuan",
    "Ca Mau", "Can Tho", "Cao Bang", "Da Nang", "Dak Lak", "Dak Nong",
    "Dien Bien", "Dong Nai", "Dong Thap", "Gia Lai", "Ha Giang", "Ha Nam",
    "Ha Noi", "Ha Tinh", "Hai Duong", "Hai Phong", "Hau Giang", "Hoa Binh",
    "Hung Yen", "Khanh Hoa", "Kien Giang", "Kon Tum", "Lai Chau", "Lam Dong",
    "Lang Son", "Lao Cai", "Long An", "Nam Dinh", "Nghe An", "Ninh Binh",
    "Ninh Thuan", "Phu Tho", "Phu Yen", "Quang Binh", "Quang Nam", "Quang Ngai",
    "Quang Ninh", "Quang Tri", "Soc Trang", "Son La", "Tay Ninh", "Thai Binh",
    "Thai Nguyen", "Thanh Hoa", "Thua Thien Hue", "Tien Giang", "Ho Chi Minh City",
    "Tra Vinh", "Tuyen Quang", "Vinh Long", "Vinh Phuc", "Yen Bai"
]

# City/district to province mapping - ONLY cities that are uniquely in one province
CITY_TO_PROVINCE = {
    # Major cities that uniquely identify provinces
    "nha trang": "Khanh Hoa",
    "cam ranh": "Khanh Hoa",
    "da lat": "Lam Dong",
    "dalat": "Lam Dong",
    "hoi an": "Quang Nam",
    "sa pa": "Lao Cai",
    "sapa": "Lao Cai",
    "ha long": "Quang Ninh",
    "phu quoc": "Kien Giang",
    "vung tau": "Ba Ria - Vung Tau",
    "con dao": "Ba Ria - Vung Tau",
    "cat ba": "Hai Phong",
    "quy nhon": "Binh Dinh",
    "phan thiet": "Binh Thuan",
    "mui ne": "Binh Thuan",
    "buon ma thuot": "Dak Lak",
    "buon me thuot": "Dak Lak",
    "tam dao": "Vinh Phuc",
    "tam coc": "Ninh Binh",
    "trang an": "Ninh Binh",
    "phong nha": "Quang Binh",
    "dong hoi": "Quang Binh",
    "phan rang": "Ninh Thuan",
    "thap cham": "Ninh Thuan",
    "pleiku": "Gia Lai",
    "cao lanh": "Dong Thap",
    "bien hoa": "Dong Nai",
    "thu dau mot": "Binh Duong",
    "tuy hoa": "Phu Yen",
    "dien bien phu": "Dien Bien",
    "uong bi": "Quang Ninh",
    "mai chau": "Hoa Binh",
    "my tho": "Tien Giang",
    "chau doc": "An Giang",
    "long xuyen": "An Giang",
    "ly son": "Quang Ngai",
    "moc chau": "Son La",
    "ba be": "Bac Kan",
    "sam son": "Thanh Hoa",
    "dong ha": "Quang Tri",
    "viet tri": "Phu Tho",
    "tam ky": "Quang Nam",
    "rach gia": "Kien Giang",
    "tan an": "Long An",
    "phu ly": "Ha Nam",
    "bac giang city": "Bac Giang",
    "thai nguyen city": "Thai Nguyen",
    "vinh yen": "Vinh Phuc",
    "thanh hoa city": "Thanh Hoa",
    "vinh city": "Nghe An",
    "ha tinh city": "Ha Tinh",
    "nam dinh city": "Nam Dinh",
    "hung yen city": "Hung Yen",
    "hai duong city": "Hai Duong",
    "ninh binh city": "Ninh Binh",
    "bac lieu city": "Bac Lieu",
    "ca mau city": "Ca Mau",
    "soc trang city": "Soc Trang",
    "tra vinh city": "Tra Vinh",
    "vinh long city": "Vinh Long",
    "ben tre city": "Ben Tre",
    "cu chi": "Ho Chi Minh City",
    "district 1": "Ho Chi Minh City",
    "district 9": "Ho Chi Minh City",
    "binh thanh": "Ho Chi Minh City",
    "thu duc": "Ho Chi Minh City",
    "go vap": "Ho Chi Minh City",
    "tan binh": "Ho Chi Minh City",
}

# Province name variations mapping
PROVINCE_VARIATIONS = {
    # An Giang
    "an giang": "An Giang",
    # Ba Ria - Vung Tau
    "ba ria - vung tau": "Ba Ria - Vung Tau",
    "ba ria vung tau": "Ba Ria - Vung Tau",
    "ba ria-vung tau": "Ba Ria - Vung Tau",
    # Bac Giang
    "bac giang": "Bac Giang",
    # Bac Kan
    "bac kan": "Bac Kan",
    "bac can": "Bac Kan",
    # Bac Lieu
    "bac lieu": "Bac Lieu",
    # Bac Ninh
    "bac ninh": "Bac Ninh",
    # Ben Tre
    "ben tre": "Ben Tre",
    # Binh Dinh
    "binh dinh": "Binh Dinh",
    # Binh Duong
    "binh duong": "Binh Duong",
    # Binh Phuoc
    "binh phuoc": "Binh Phuoc",
    # Binh Thuan
    "binh thuan": "Binh Thuan",
    # Ca Mau
    "ca mau": "Ca Mau",
    # Can Tho
    "can tho": "Can Tho",
    # Cao Bang
    "cao bang": "Cao Bang",
    # Da Nang
    "da nang": "Da Nang",
    # Dak Lak
    "dak lak": "Dak Lak",
    "daklak": "Dak Lak",
    "dac lac": "Dak Lak",
    # Dak Nong
    "dak nong": "Dak Nong",
    "daknong": "Dak Nong",
    # Dien Bien
    "dien bien": "Dien Bien",
    # Dong Nai
    "dong nai": "Dong Nai",
    # Dong Thap
    "dong thap": "Dong Thap",
    # Gia Lai
    "gia lai": "Gia Lai",
    # Ha Giang
    "ha giang": "Ha Giang",
    # Ha Nam
    "ha nam": "Ha Nam",
    # Ha Noi
    "ha noi": "Ha Noi",
    "hanoi": "Ha Noi",
    # Ha Tinh
    "ha tinh": "Ha Tinh",
    # Hai Duong
    "hai duong": "Hai Duong",
    # Hai Phong
    "hai phong": "Hai Phong",
    # Hau Giang
    "hau giang": "Hau Giang",
    # Hoa Binh
    "hoa binh": "Hoa Binh",
    # Ho Chi Minh City
    "ho chi minh": "Ho Chi Minh City",
    "ho chi minh city": "Ho Chi Minh City",
    "hcmc": "Ho Chi Minh City",
    "saigon": "Ho Chi Minh City",
    # Hung Yen
    "hung yen": "Hung Yen",
    # Khanh Hoa
    "khanh hoa": "Khanh Hoa",
    # Kien Giang
    "kien giang": "Kien Giang",
    # Kon Tum
    "kon tum": "Kon Tum",
    # Lai Chau
    "lai chau": "Lai Chau",
    # Lam Dong
    "lam dong": "Lam Dong",
    # Lang Son
    "lang son": "Lang Son",
    # Lao Cai
    "lao cai": "Lao Cai",
    # Long An
    "long an": "Long An",
    # Nam Dinh
    "nam dinh": "Nam Dinh",
    # Nghe An
    "nghe an": "Nghe An",
    # Ninh Binh
    "ninh binh": "Ninh Binh",
    # Ninh Thuan
    "ninh thuan": "Ninh Thuan",
    # Phu Tho
    "phu tho": "Phu Tho",
    # Phu Yen
    "phu yen": "Phu Yen",
    # Quang Binh
    "quang binh": "Quang Binh",
    # Quang Nam
    "quang nam": "Quang Nam",
    # Quang Ngai
    "quang ngai": "Quang Ngai",
    # Quang Ninh
    "quang ninh": "Quang Ninh",
    # Quang Tri
    "quang tri": "Quang Tri",
    # Soc Trang
    "soc trang": "Soc Trang",
    # Son La
    "son la": "Son La",
    # Tay Ninh
    "tay ninh": "Tay Ninh",
    # Thai Binh
    "thai binh": "Thai Binh",
    # Thai Nguyen
    "thai nguyen": "Thai Nguyen",
    # Thanh Hoa
    "thanh hoa": "Thanh Hoa",
    # Thua Thien Hue
    "thua thien hue": "Thua Thien Hue",
    "thua thien-hue": "Thua Thien Hue",
    "hue city": "Thua Thien Hue",
    # Tien Giang
    "tien giang": "Tien Giang",
    # Tra Vinh
    "tra vinh": "Tra Vinh",
    # Tuyen Quang
    "tuyen quang": "Tuyen Quang",
    # Vinh Long
    "vinh long": "Vinh Long",
    # Vinh Phuc
    "vinh phuc": "Vinh Phuc",
    # Yen Bai
    "yen bai": "Yen Bai",
}


def find_province_in_text(text):
    """
    Find province mentioned in text with explicit location context.
    Returns (province, confidence) or (None, 0)
    """
    text_lower = text.lower()
    
    # Pattern 1: "Location: X district/commune, Y province" (highest confidence)
    location_patterns = [
        r'location[:\s]+([^,\.]+(?:district|commune|ward|city)[^,\.]*,\s*)?([a-z\s\-]+)\s+province',
        r'located in[:\s]+([^,\.]+(?:district|commune|ward|city)[^,\.]*,\s*)?([a-z\s\-]+)\s+province',
        r'in\s+([a-z\s\-]+)\s+province',
        r'([a-z\s\-]+)\s+province',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Get the province part (last group)
            province_text = match.groups()[-1].strip()
            if province_text in PROVINCE_VARIATIONS:
                return (PROVINCE_VARIATIONS[province_text], 10)
    
    # Pattern 2: Specific city mentions that uniquely identify a province
    for city, province in CITY_TO_PROVINCE.items():
        # Look for city name with word boundaries
        pattern = r'\b' + re.escape(city) + r'\b'
        if re.search(pattern, text_lower):
            return (province, 8)
    
    # Pattern 3: Province name directly mentioned
    # Sort by length to match longer names first (e.g., "Ho Chi Minh City" before "Chi")
    sorted_variations = sorted(PROVINCE_VARIATIONS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for variation, standard in sorted_variations:
        pattern = r'\b' + re.escape(variation) + r'\b'
        if re.search(pattern, text_lower):
            return (standard, 5)
    
    return (None, 0)


def extract_province_from_description(description):
    """
    Extract province from description, focusing on explicit location mentions.
    """
    if not description:
        return None
    
    # Convert description list to string if needed
    if isinstance(description, list):
        description = " ".join(description)
    
    # First check the beginning of the description (first 300 chars) - usually has location
    first_part = description[:500]
    province, confidence = find_province_in_text(first_part)
    
    if province and confidence >= 8:
        return province
    
    # Check the full description
    full_province, full_confidence = find_province_in_text(description)
    
    if full_province:
        # If we found something in first part and full, prefer first part
        if province and confidence >= 5:
            return province
        return full_province
    
    return province


def normalize_tag_province(tag):
    """Normalize the current tag to standard province name"""
    if not tag:
        return None
    
    tag_lower = tag.lower().strip()
    
    # Check exact match with standard provinces
    for province in STANDARD_PROVINCES:
        if tag_lower == province.lower():
            return province
    
    # Check variations
    if tag_lower in PROVINCE_VARIATIONS:
        return PROVINCE_VARIATIONS[tag_lower]
    
    # Check if it's a well-known city
    if tag_lower in CITY_TO_PROVINCE:
        return CITY_TO_PROVINCE[tag_lower]
    
    return tag


def fix_province_tags():
    """Main function to fix province tags in the database"""
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vietnamtravel.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, tags, description FROM place')
    places = cursor.fetchall()
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    not_found_count = 0
    
    print(f"Processing {len(places)} places...")
    print("-" * 80)
    
    changes = []
    
    for idx, (place_id, name, tags_str, description_str) in enumerate(places):
        try:
            tags = json.loads(tags_str) if tags_str else []
            if not tags:
                skipped_count += 1
                continue
            
            current_province_tag = tags[0]
            
            description = json.loads(description_str) if description_str else ""
            if isinstance(description, list):
                description = " ".join(description)
            
            # Extract province from description
            new_province = extract_province_from_description(description)
            
            if not new_province:
                # Keep the original if we can't determine from description
                not_found_count += 1
                continue
            
            # Normalize current tag for comparison
            normalized_current = normalize_tag_province(current_province_tag)
            
            # Only update if different
            if normalized_current != new_province:
                tags[0] = new_province
                new_tags_str = json.dumps(tags, ensure_ascii=False)
                
                cursor.execute(
                    'UPDATE place SET tags = ? WHERE id = ?',
                    (new_tags_str, place_id)
                )
                
                changes.append((idx+1, name, current_province_tag, new_province))
                updated_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"[{idx+1}/{len(places)}] Error processing {name}: {e}")
            error_count += 1
    
    conn.commit()
    conn.close()
    
    # Print all changes
    for idx, name, old_prov, new_prov in changes:
        print(f"[{idx}/{len(places)}] Updated '{name}': '{old_prov}' -> '{new_prov}'")
    
    print("-" * 80)
    print(f"Summary:")
    print(f"  Total places: {len(places)}")
    print(f"  Updated: {updated_count}")
    print(f"  Already correct: {skipped_count}")
    print(f"  Could not determine (kept original): {not_found_count}")
    print(f"  Errors: {error_count}")


if __name__ == "__main__":
    fix_province_tags()
