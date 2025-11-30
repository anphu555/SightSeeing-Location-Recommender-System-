import json
import csv
import asyncio
from groq import Groq
from fastapi.concurrency import run_in_threadpool
import time
from datetime import datetime



# ====== CSV translate ======
INPUT_CSV = "data896-899.csv"
OUTPUT_CSV = "data896-899_en.csv"
CHECKPOINT_CSV = "data896-899_en.csv"


# ====== CONFIG ======
API_KEY = "GROQ_API_KEY"
# MODEL = "llama-3.3-70b-versatile"
# MODEL = "qwen/qwen3-32b"
MODEL = "openai/gpt-oss-120b"



# Rate limiting - ƯU TIÊN TPD (Tokens Per Day)
MAX_TOKENS_PER_DAY = 95000  # Giới hạn 95k/100k để an toàn
ESTIMATED_TOKENS_PER_ROW = 150  # Ước tính token cho mỗi row
MAX_ROWS_PER_DAY = MAX_TOKENS_PER_DAY // ESTIMATED_TOKENS_PER_ROW  # ~633 rows/day

# Rate limiting thứ cấp
MAX_RPM = 25
BATCH_SIZE = 25
DELAY_BETWEEN_BATCHES = 65

client = Groq(api_key=API_KEY)

SYSTEM_PROMPT = """
You are a professional travel writer and translator specializing in Vietnamese tourism content for international audiences.

TRANSLATION PRINCIPLES:
1. Write naturally for native English speakers - avoid literal translations
2. Use engaging, descriptive language that inspires travel
3. Simplify complex Vietnamese cultural terms with brief explanations
4. Break long sentences into shorter, readable ones
5. Keep the tone warm, inviting, and informative
6. Preserve specific names of places, but skip the marks in Vietnamese and translate their meanings in parentheses when helpful

SPECIFIC GUIDELINES:
- Historical dates: Use simple format "built in 1070" instead of "the second year of Thien Vu reign"
- Vietnamese terms: Either translate them or keep the term with a brief English explanation
- Measurements: Keep meters (m), hectares (ha) as-is
- Species names: Use common English names, scientific names in parentheses only if important
- Architecture terms: Use simple English equivalents (e.g., "pagoda" not "chùa")
- Preserve "|||" separators exactly as-is

CRITICAL CSV FORMATTING RULES:
- DO NOT add line breaks or indentation in the description
- Each paragraph/section should be separated ONLY by "|||"
- Write continuously without pressing Enter/Return
- Use single spaces between words, no extra whitespace

OUTPUT FORMAT:
- Only translate "title" and "description" fields
- Output MUST be valid JSON only - no markdown, no extra text
- NO line breaks inside description text
- Preserve all "|||" separators
- If a field is empty, leave it empty

GOOD EXAMPLES:

Input: {"title": "Chùa Một Cột", "description": "Chùa Một Cột được xây dựng năm 1049 dưới thời vua Lý Thái Tông. Chùa có hình dạng độc đáo như bông sen nở trên mặt nước."}
Output: {"title": "One Pillar Pagoda", "description": "Built in 1049 under Emperor Ly Thai Tong, this unique pagoda rises from the water like a lotus blossom in full bloom."}

Input: {"title": "Rừng tràm Trà Sư", "description": "Rừng tràm Trà Sư có diện tích gần 850ha, là nơi sinh sống của 70 loài chim thuộc 13 bộ và 31 họ.|||Mùa nước nổi là thời điểm đẹp nhất để thăm rừng."}
Output: {"title": "Tra Su Cajuput Forest", "description": "Spanning nearly 850 hectares, Tra Su Forest is a sanctuary for 70 bird species, creating a paradise for nature lovers and birdwatchers.|||The flooding season is the best time to visit the forest."}

Now translate this input JSON:
"""


def _call_groq(user_text: str):
    if not API_KEY:
        raise Exception("GROQ_API_KEY is missing")
        
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        max_tokens=4000,  # ✅ QUAN TRỌNG: Tăng limit để dịch hết description dài
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    content = completion.choices[0].message.content
    
    # Lấy thông tin token usage
    usage = completion.usage
    return json.loads(content), usage


async def extract_with_groq(user_text: str):
    try:
        data, usage = await run_in_threadpool(_call_groq, user_text)
        return data, usage
    except Exception as e:
        error_msg = str(e)
        if "rate_limit_exceeded" in error_msg:
            print(f"\n🚫 RATE LIMIT HIT!")
            if "tokens per day" in error_msg.lower():
                print(f"   TPD limit reached. Need to wait or upgrade.")
            elif "requests per minute" in error_msg.lower():
                print(f"   RPM limit reached. Slowing down...")
        print(f"❌ Error: {error_msg[:200]}")
        return None, None





async def translate_csv(max_rows=None):
    """
    Dịch CSV với token tracking và rate limiting
    
    Args:
        max_rows: Số dòng tối đa muốn dịch (None = không giới hạn)
    """
    
    # Đọc tất cả rows
    print(f"📖 Reading {INPUT_CSV}...")
    all_rows = []
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
    
    total_rows = len(all_rows)
    print(f"✅ Found {total_rows} rows")
    
    # Áp dụng giới hạn nếu có
    if max_rows:
        total_rows = min(total_rows, max_rows)
        all_rows = all_rows[:total_rows]
        print(f"⚠️  Limiting to {total_rows} rows (token budget)")
    
    # Kiểm tra checkpoint
    translated_rows = []
    start_index = 0
    total_tokens_used = 0
    
    try:
        with open(CHECKPOINT_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            translated_rows = list(reader)
            start_index = len(translated_rows)
            print(f"📌 Resuming from row {start_index}")
    except FileNotFoundError:
        print("🆕 Starting fresh translation")
    
    # Token tracking
    print(f"\n💡 Token budget: {MAX_TOKENS_PER_DAY:,} tokens/day")
    print(f"💡 Estimated: ~{ESTIMATED_TOKENS_PER_ROW} tokens/row")
    print(f"💡 Safe limit: {MAX_ROWS_PER_DAY} rows/day")
    
    # Dịch từng batch
    for batch_num in range(start_index // BATCH_SIZE, (total_rows + BATCH_SIZE - 1) // BATCH_SIZE):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, total_rows)
        batch_rows = all_rows[batch_start:batch_end]
        
        print(f"\n{'='*60}")
        print(f"🔄 Batch {batch_num + 1} (rows {batch_start + 1}-{batch_end})")
        print(f"   Tokens used so far: {total_tokens_used:,}")
        print(f"{'='*60}")
        
        batch_start_time = time.time()
        batch_tokens = 0
        
        # Dịch từng row
        for i, row in enumerate(batch_rows):
            current_row = batch_start + i + 1
            
            title = row.get("title", "")
            desc = row.get("description", "")
            
            # ✅ KIỂM TRA description dài
            desc_length = len(desc)
            if desc_length > 3000:
                print(f"  ⚠️  Row {current_row}: Long description ({desc_length} chars), splitting...")
                
                # Chia description theo separator "|||"
                desc_parts = desc.split("|||")
                translated_parts = []
                
                for part_idx, part in enumerate(desc_parts):
                    if not part.strip():
                        translated_parts.append("")
                        continue
                        
                    json_text = json.dumps({
                        "title": "" if part_idx > 0 else title,  # Chỉ dịch title ở part đầu
                        "description": part.strip()
                    }, ensure_ascii=False)
                    
                    translated, usage = await extract_with_groq(json_text)
                    
                    if translated and usage:
                        batch_tokens += usage.total_tokens
                        total_tokens_used += usage.total_tokens
                        translated_parts.append(translated.get("description", part))
                        
                        if part_idx == 0 and translated.get("title"):
                            title = translated.get("title")
                        
                        print(f"     Part {part_idx + 1}/{len(desc_parts)}: {usage.total_tokens} tokens")
                    else:
                        translated_parts.append(part)
                    
                    # Delay nhỏ giữa các parts
                    await asyncio.sleep(0.5)
                
                # Merge lại
                new_row = row.copy()
                new_row["title"] = title
                new_row["description"] = "|||".join(translated_parts)
                translated_rows.append(new_row)
                
                print(f"  ✅ Row {current_row}/{total_rows}: {title[:40]}... (split into {len(desc_parts)} parts)")
                
            else:
                # Description ngắn - dịch bình thường
                json_text = json.dumps({
                    "title": title,
                    "description": desc
                }, ensure_ascii=False)
                
                translated, usage = await extract_with_groq(json_text)
                
                if translated and usage:
                    batch_tokens += usage.total_tokens
                    total_tokens_used += usage.total_tokens
                    
                    new_row = row.copy()
                    new_row["title"] = translated.get("title", title)
                    new_row["description"] = translated.get("description", desc)
                    translated_rows.append(new_row)
                    
                    title_preview = new_row['title'][:40] + "..." if len(new_row['title']) > 40 else new_row['title']
                    print(f"  ✅ Row {current_row}/{total_rows}: {title_preview}")
                    print(f"     Tokens: {usage.total_tokens} (total: {total_tokens_used:,})")
                else:
                    translated_rows.append(row)
                    print(f"  ⚠️  Row {current_row}/{total_rows}: Failed, keeping original")
            
            # KIỂM TRA token limit
            if total_tokens_used >= MAX_TOKENS_PER_DAY:
                print(f"\n⚠️  TOKEN LIMIT REACHED ({total_tokens_used:,}/{MAX_TOKENS_PER_DAY:,})")
                print(f"   Saving progress and stopping...")
                save_checkpoint(translated_rows)
                save_final_output(translated_rows)
                print(f"\n📊 Translated {len(translated_rows)}/{len(all_rows)} rows")
                print(f"💾 Resume tomorrow or upgrade plan!")
                return
            
            # Lưu checkpoint mỗi 5 rows
            if current_row % 5 == 0:
                save_checkpoint(translated_rows)
        
        # Batch summary
        batch_elapsed = time.time() - batch_start_time
        print(f"\n📊 Batch summary:")
        print(f"   Tokens used: {batch_tokens}")
        print(f"   Time: {batch_elapsed:.1f}s")
        
        # Delay giữa các batch
        if batch_end < total_rows:
            wait_time = max(0, DELAY_BETWEEN_BATCHES - batch_elapsed)
            if wait_time > 0:
                print(f"⏳ Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
    
    # Lưu kết quả cuối
    save_final_output(translated_rows)
    
    # ✅ VALIDATION: Kiểm tra số cột
    print(f"\n🔍 Validating output CSV...")
    try:
        with open(OUTPUT_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            output_rows = list(reader)
            
        print(f"✅ Validation passed:")
        print(f"   Input rows: {len(all_rows)}")
        print(f"   Output rows: {len(output_rows)}")
        print(f"   Columns: {list(output_rows[0].keys()) if output_rows else 'N/A'}")
        
        # Kiểm tra cột
        if output_rows:
            expected_cols = list(all_rows[0].keys())
            actual_cols = list(output_rows[0].keys())
            if expected_cols != actual_cols:
                print(f"⚠️  WARNING: Column mismatch!")
                print(f"   Expected: {expected_cols}")
                print(f"   Got: {actual_cols}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    print(f"\n🎉 Translation complete!")
    print(f"📊 Final stats:")
    print(f"   Rows: {len(translated_rows)}/{len(all_rows)}")
    print(f"   Tokens: {total_tokens_used:,}")


def save_checkpoint(rows):
    """Lưu checkpoint - ĐẢM BẢO format CSV đúng"""
    if rows:
        fieldnames = rows[0].keys()
        with open(CHECKPOINT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in rows:
                # ✅ Làm sạch description: xóa xuống dòng không mong muốn
                if 'description' in row:
                    desc = row['description']
                    # Giữ nguyên separator "|||", nhưng xóa \n trong mỗi phần
                    parts = desc.split('|||')
                    cleaned_parts = []
                    for part in parts:
                        # Xóa xuống dòng, giữ một khoảng trắng
                        cleaned = ' '.join(part.split())
                        cleaned_parts.append(cleaned)
                    row['description'] = '|||'.join(cleaned_parts)
                
                writer.writerow(row)


def save_final_output(rows):
    """Lưu file cuối cùng - ĐẢM BẢO format CSV đúng"""
    if rows:
        fieldnames = rows[0].keys()
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in rows:
                # ✅ Làm sạch description
                if 'description' in row:
                    desc = row['description']
                    parts = desc.split('|||')
                    cleaned_parts = []
                    for part in parts:
                        cleaned = ' '.join(part.split())
                        cleaned_parts.append(cleaned)
                    row['description'] = '|||'.join(cleaned_parts)
                
                writer.writerow(row)
        print(f"💾 Saved to {OUTPUT_CSV}")


# ====== Run ======
if __name__ == "__main__":
    print("=" * 60)
    print("🌏 VIETNAM PLACES CSV TRANSLATOR")
    print("=" * 60)
    print(f"⚙️  Model: {MODEL}")
    print(f"⚙️  Token limit: {MAX_TOKENS_PER_DAY:,}/day")
    print(f"⚙️  Safe rows/day: ~{MAX_ROWS_PER_DAY}")
    print("=" * 60)
    
    # TÙY CHỌN: Giới hạn số dòng dịch mỗi lần chạy
    # Uncomment dòng dưới nếu muốn dịch tối đa N dòng/ngày
    # MAX_ROWS_TO_TRANSLATE = 600  
    MAX_ROWS_TO_TRANSLATE = None  # None = dịch hết (đến khi hết token)
    
    start_time = datetime.now()
    asyncio.run(translate_csv(max_rows=MAX_ROWS_TO_TRANSLATE))
    end_time = datetime.now()
    
    elapsed = (end_time - start_time).total_seconds()
    print(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")