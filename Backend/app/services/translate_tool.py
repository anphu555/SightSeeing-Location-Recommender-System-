import pandas as pd
import google.generativeai as genai
import json
import time

# ======= CONFIG =======
genai.configure(api_key="MY_API_KEY")
model = genai.GenerativeModel("gemini-2.5-flash")

INPUT_CSV = "vietnam_tourism_data.csv"
OUTPUT_CSV = "vietnam_tourism_data_en.csv"

BATCH_SIZE = 3          # nhỏ hơn để text dài không quá tải
MAX_RPM = 10
MIN_INTERVAL = 60 / MAX_RPM
RETRY = 3
RETRY_DELAY = 10
# =======================


def split_description(description):
    """Tách description thành các đoạn theo '|||' """
    return [seg.strip() for seg in description.split("|||") if seg.strip()]


def build_prompt(batch, start_idx):
    items = []
    for offset, row in enumerate(batch):
        idx = start_idx + offset
        desc_segments = split_description(row["description"])
        items.append({
            "id": idx,
            "title": row["title"],
            "description_segments": desc_segments
        })

    prompt = f"""
Translate the following Vietnamese places to English, skip the marks in Vietnamese.
Translate the 'title' fully.
For 'description_segments', translate each segment in order, keeping meaning.
Do NOT add anything extra.
Return ONLY a valid JSON array with this format:

[
  {{
    "id": number,
    "title_en": "translated",
    "description_en": "translated full description (all segments joined with spaces)"
  }}
]

Here is the input JSON:

{json.dumps(items, ensure_ascii=False, indent=2)}
    """
    return prompt


def safe_call_gemini(prompt):
    attempts = 0
    while attempts < RETRY:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            attempts += 1
            print(f"Retry {attempts}/{RETRY} - Error: {e}")
            time.sleep(RETRY_DELAY)
    return None


def ensure_rate_limit(last_call):
    if last_call is None:
        return time.time()
    elapsed = time.time() - last_call
    wait_time = MIN_INTERVAL - elapsed
    if wait_time > 0:
        print(f"Rate limit → waiting {wait_time:.1f}s")
        time.sleep(wait_time)
    return time.time()


def main():
    df = pd.read_csv(INPUT_CSV)
    total = len(df)
    print("Total rows:", total)

    results = [None] * total
    last_call = None

    image_columns = [col for col in df.columns if col.startswith("image")]

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_rows = [df.iloc[i] for i in range(start, end)]
        print(f"\nProcessing batch {start} → {end - 1}")

        prompt = build_prompt(batch_rows, start)
        last_call = ensure_rate_limit(last_call)
        text = safe_call_gemini(prompt)

        if text is None:
            print("❌ Batch failed permanently!")
            continue

        # parse JSON
        try:
            data = json.loads(text)
        except Exception:
            print("❌ Invalid JSON — trying relaxed parsing...")
            cleaned = text[text.find("[") : text.rfind("]") + 1]
            try:
                data = json.loads(cleaned)
            except Exception:
                print("❌ Still invalid JSON → batch skipped.")
                continue

        # store results
        for item in data:
            idx = item["id"]
            new_row = {
                "id": df.at[idx, "id"],
                "title_en": item.get("title_en", ""),
                "description_en": item.get("description_en", "")
            }
            for ic in image_columns:
                new_row[ic] = df.at[idx, ic]
            results[idx] = new_row

    df_out = pd.DataFrame(results)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print("\n🎉 DONE! Saved to", OUTPUT_CSV)


if __name__ == "__main__":
    main()
