import pandas as pd
import os
import re

SCORED_PATH = 'output/scored_hosts.csv'
FINAL_XLSX = 'output/final_results.xlsx'
HOST2ME_XLSX = 'output/host2me_results.xlsx'
HOST2ME_JSON = 'output/host2me_results.json'
REVIEW_CSV = 'output/review_queue.csv'
REJECTED_CSV = 'output/rejected_log.csv'

# Helper: sanitize and truncate fields for Excel

def sanitize_for_excel(val, maxlen=500):
    if pd.isna(val):
        return ''
    val = str(val)
    # Replace | and : with safe chars
    val = val.replace('|', '¦').replace(':', ';')
    # Remove control characters
    val = re.sub(r'[\x00-\x1F\x7F]', '', val)
    # Truncate if too long
    if len(val) > maxlen:
        val = val[:maxlen] + '...'
    return val

def main():
    if not os.path.exists(SCORED_PATH):
        print(f"[ERROR] {SCORED_PATH} not found. Run scoring_pass.py first.")
        return
    df = pd.read_csv(SCORED_PATH)
    for col in ['links', 'snippets', 'reason', 'title', 'meta_description']:
        if col in df.columns:
            df[col] = df[col].apply(sanitize_for_excel)
    accepted = df[df['status'] == 'Accepted']
    review = df[df['status'] == 'Review']
    rejected = df[df['status'] == 'Rejected']

    if accepted.empty:
        print("[WARN] No accepted companies found in scored data. Check scoring thresholds or filters.")

    os.makedirs('output', exist_ok=True)
    accepted.to_excel(FINAL_XLSX, index=False)
    accepted.to_excel(HOST2ME_XLSX, index=False)
    accepted.to_json(HOST2ME_JSON, orient='records', force_ascii=False)
    review.to_csv(REVIEW_CSV, index=False)
    rejected.to_csv(REJECTED_CSV, index=False)

    print(f"[EXPORT] {len(accepted)} accepted → {FINAL_XLSX}")
    print(f"[EXPORT] {len(accepted)} accepted → {HOST2ME_XLSX} & {HOST2ME_JSON}")
    print(f"[EXPORT] {len(review)} for review → {REVIEW_CSV}")
    print(f"[EXPORT] {len(rejected)} rejected → {REJECTED_CSV}")
    print("[EXPORT] Done.")

    # Placeholder: LLM/manual review integration for review queue
    # for idx, row in review.iterrows():
    #     print(f"[REVIEW] {row['url']} | {row['reason']}")
    #     # TODO: Integrate with LLM or prompt for human input

if __name__ == '__main__':
    main() 