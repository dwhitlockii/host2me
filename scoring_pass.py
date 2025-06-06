import pandas as pd
import re
import tldextract
import os

RAW_PATH = 'output/unfiltered_hosts.csv'
SCORED_PATH = 'output/scored_hosts.csv'
DEBUG_PATH = 'output/company_score_debug.csv'

PRIMARY_KEYWORDS = [
    'web hosting', 'dedicated server', 'cloud hosting', 'vps hosting', 'shared hosting', 'hosting provider'
]
SECONDARY_KEYWORDS = [
    'infrastructure', 'scalable solutions', 'enterprise hosting', 'platform', 'managed', 'cloud web', 'virtual server'
]
CONTEXT_MODIFIERS = [
    'plans', 'pricing', 'datacenter', 'uptime', 'specs', 'features', 'tiers', 'comparison', 'sla'
]
TECH_KEYWORDS = [
    'cpanel', 'plesk', 'whmcs', 'blesta', 'clientexec', 'kvm', 'xen', 'docker', 'kubernetes', 'aws', 'azure', 'google cloud'
]
NEGATIVE_KEYWORDS = [
    'affiliate program', 'top 10 hosts', 'powered by godaddy', 'review aggregator', 'directory', 'comparison', 'blog', 'news', 'coupon', 'deal', 'forum', 'reddit', 'quora', 'wikipedia', 'list of', 'best hosting'
]

NAV_PATTERNS = ['/pricing', '/plans', '/hosting', '/servers', '/cloud', '/support', '/kb', '/docs', '/datacenter', '/infrastructure', '/network']
CTA_VERBS = ['buy', 'start', 'launch', 'signup', 'quote', 'order', 'get started', 'register']

ACCEPT_THRESHOLD = 30
RESCUE_THRESHOLD = 20

# Helper: count strong signals

def count_strong_signals(row, snippets, links):
    strong = 0
    # Careers/jobs link
    if any('career' in l or 'job' in l for l in links):
        strong += 1
    # Tech keyword
    if any(tk in s for tk in TECH_KEYWORDS for s in snippets):
        strong += 1
    # Multiple secondary/contextual
    sec_count = 0
    for sec in SECONDARY_KEYWORDS:
        for snip in snippets:
            if sec in snip:
                for mod in CONTEXT_MODIFIERS:
                    if mod in snip:
                        sec_count += 1
    if sec_count >= 2:
        strong += 1
    return strong

def score_row(row):
    score = 0
    reasons = []
    # Content signals
    title = str(row['title'] or '').lower()
    meta = str(row['meta_description'] or '').lower()
    snippets = str(row['snippets'] or '').lower().split('|') if row['snippets'] and not pd.isna(row['snippets']) else []
    links = str(row['links'] or '').lower().split('|') if row['links'] and not pd.isna(row['links']) else []
    # Primary keywords
    for kw in PRIMARY_KEYWORDS:
        if kw in title or kw in meta:
            score += 15
            reasons.append(f"Primary keyword '{kw}' in title/meta (+15)")
        for snip in snippets:
            if kw in snip:
                score += 15
                reasons.append(f"Primary keyword '{kw}' in snippet (+15)")
    # Secondary/contextual
    sec_count = 0
    for sec in SECONDARY_KEYWORDS:
        for snip in snippets:
            if sec in snip:
                for mod in CONTEXT_MODIFIERS:
                    if mod in snip:
                        score += 15
                        sec_count += 1
                        reasons.append(f"Secondary keyword '{sec}' with context '{mod}' (+15)")
    # Tech stack (boosted)
    for tech in TECH_KEYWORDS:
        if tech in title or tech in meta or any(tech in snip for snip in snippets):
            score += 10
            reasons.append(f"Tech keyword '{tech}' (+10)")
    # Nav patterns (add for each match)
    nav_matches = 0
    for nav in NAV_PATTERNS:
        nav_count = sum(nav in l for l in links)
        if nav_count:
            score += 10 * nav_count
            nav_matches += nav_count
            reasons.append(f"Nav pattern '{nav}' x{nav_count} (+{10*nav_count})")
    # CTA verbs (add for each match)
    cta_matches = 0
    for cta in CTA_VERBS:
        cta_count = sum(cta in l for l in links)
        if cta_count:
            score += 10 * cta_count
            cta_matches += cta_count
            reasons.append(f"CTA verb '{cta}' x{cta_count} (+{10*cta_count})")
    # Pricing/plans/uptime/SLAs in visible text (boosted)
    for mod in CONTEXT_MODIFIERS:
        mod_count = sum(mod in snip for snip in snippets)
        if mod_count:
            score += 10 * mod_count
            reasons.append(f"Modifier '{mod}' x{mod_count} (+{10*mod_count})")
    # Aggregate signals from links/snippets mentioning 'hosting', 'plans', 'cloud', etc.
    agg_terms = ['hosting', 'plans', 'cloud']
    agg_count = 0
    for term in agg_terms:
        agg_count += sum(term in l for l in links)
        agg_count += sum(term in snip for snip in snippets)
    if agg_count >= 2:
        score += 10
        reasons.append(f"Aggregated signals for {agg_count} hosting/plans/cloud (+10)")
    # Negative signals
    for neg in NEGATIVE_KEYWORDS:
        if neg in title or neg in meta or any(neg in snip for snip in snippets):
            score -= 50
            reasons.append(f"Negative keyword '{neg}' (-50)")
    # Short content
    word_count = sum(len(snip.split()) for snip in snippets)
    if word_count < 300:
        score -= 20
        reasons.append("Short content (<300 words) (-20)")
    # Rescue logic: If score 20–30 and at least two strong signals, flag as 'Rescued'
    strong_signals = count_strong_signals(row, snippets, links)
    if score >= ACCEPT_THRESHOLD:
        status = 'Accepted'
        confidence = 'High'
    elif RESCUE_THRESHOLD <= score < ACCEPT_THRESHOLD and strong_signals >= 2:
        status = 'Rescued'
        confidence = 'Medium'
        reasons.append(f"Rescued: {strong_signals} strong signals")
    elif RESCUE_THRESHOLD <= score < ACCEPT_THRESHOLD:
        status = 'Review'
        confidence = 'Medium'
    else:
        status = 'Rejected'
        confidence = 'Low'
    reason_summary = '; '.join(reasons)
    return score, confidence, status, reason_summary

def main():
    if not os.path.exists(RAW_PATH):
        print(f"[ERROR] {RAW_PATH} not found. Run foundational_scrape() first.")
        return
    df = pd.read_csv(RAW_PATH)
    results = []
    debug_rows = []
    for _, row in df.iterrows():
        score, confidence, status, reason = score_row(row)
        results.append({
            **row,
            'score': score,
            'confidence': confidence,
            'status': status,
            'reason': reason
        })
        decision_label = {
            'Accepted': '✅ ADDED',
            'Rescued': '⚠️ BORDERLINE',
            'Review': '🤔 REVIEW',
            'Rejected': '❌ SKIPPED'
        }.get(status, status)
        print(f"[INFO] Scored {row.get('base_domain') or row.get('url')} — Score: {score} {decision_label}")
        if reason:
            print(f"[DEBUG] Reasons: {reason}")
        debug_rows.append({
            'name': row.get('base_domain'),
            'url': row.get('url'),
            'score': score,
            'decision': status,
            'reason': reason
        })
    out_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(SCORED_PATH), exist_ok=True)
    out_df.to_csv(SCORED_PATH, index=False)
    debug_df = pd.DataFrame(debug_rows)
    debug_df.to_csv(DEBUG_PATH, index=False)
    print(f"[SCORE] Scoring complete. {len(out_df)} rows written to {SCORED_PATH}")
    print(f"[SCORE] Debug scores written to {DEBUG_PATH}")

if __name__ == '__main__':
    main() 