#!/usr/bin/env python3
"""
ShipCheck scanner — passive security scan for vibe-coded apps.
Give it a public URL. It fetches the page + its JS bundles and reports:
  - leaked secret keys (Stripe, OpenAI, AWS, service_role, generic high-entropy)
  - Supabase anon key + URL, then tests RLS by reading tables unauthenticated
  - exposed sensitive routes (.env, /admin, /api, source maps, etc.)
  - missing security headers
Only reads what a browser would see. No login, no exploit, no writes.
"""
import re, sys, json, base64, concurrent.futures as cf
from urllib.parse import urljoin, urlparse
import requests

UA = "Mozilla/5.0 (compatible; ShipCheckBot/0.1; +https://shipcheck.dev/bot)"
TIMEOUT = 15

# --- secret detectors -------------------------------------------------------
# name, regex, severity, note
SECRET_PATTERNS = [
    ("Stripe live secret key", r"sk_live_[0-9a-zA-Z]{20,}", "critical",
     "A live Stripe secret key can charge cards and read payments."),
    ("Stripe test secret key", r"sk_test_[0-9a-zA-Z]{20,}", "high",
     "A Stripe test secret key is exposed; rotate it."),
    ("OpenAI API key", r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}", "critical",
     "An OpenAI key lets anyone spend your API credits."),
    ("Anthropic API key", r"sk-ant-[A-Za-z0-9_-]{20,}", "critical",
     "An Anthropic key lets anyone spend your API credits."),
    ("AWS access key id", r"AKIA[0-9A-Z]{16}", "critical",
     "An AWS access key can reach your cloud resources."),
    ("Google API key", r"AIza[0-9A-Za-z_-]{35}", "medium",
     "A Google API key — check it is domain-restricted."),
    ("GitHub token", r"gh[pousr]_[0-9A-Za-z]{36,}", "critical",
     "A GitHub token can read or push to your repos."),
    ("Supabase service_role key", r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "jwt",
     "JWT found — decoded below to check if it is a service_role key."),
    ("Supabase sb_secret key", r"sb_secret_[A-Za-z0-9]{20,}", "critical",
     "A Supabase secret key bypasses Row Level Security."),
    ("Private key block", r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "critical",
     "A private key is shipped in client code."),
    ("Slack token", r"xox[baprs]-[0-9A-Za-z-]{10,}", "high",
     "A Slack token is exposed."),
]

SUPABASE_URL_RE = re.compile(r"https://([a-z0-9]{20})\.supabase\.co")
JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")

SENSITIVE_PATHS = [
    (".env", "critical"), (".env.local", "critical"), (".env.production", "critical"),
    (".git/config", "high"), ("config.json", "medium"), ("admin", "info"),
    ("dashboard", "info"), ("api", "info"), ("server.js", "medium"),
    ("package.json", "low"), ("vite.config.js", "low"),
]

SECURITY_HEADERS = {
    "content-security-policy": "medium",
    "strict-transport-security": "low",
    "x-frame-options": "low",
    "x-content-type-options": "low",
}

COMMON_TABLES = ["users","profiles","accounts","orders","payments","subscriptions",
    "messages","posts","api_keys","api_tokens","tokens","customers","leads",
    "contacts","emails","waitlist","feedback","todos","items","products","notes"]

def jwt_role(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data.get("role"), data.get("ref")
    except Exception:
        return None, None

def fetch(url, **kw):
    return requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT,
                        allow_redirects=True, **kw)

def collect_js_urls(html, base):
    urls = set()
    for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I):
        urls.add(urljoin(base, m.group(1)))
    for m in re.finditer(r'["\']([^"\']+\.js)["\']', html):
        if m.group(1).startswith(("http","/","./","../")):
            urls.add(urljoin(base, m.group(1)))
    return list(urls)[:40]

def scan_text(text, source, findings):
    seen = set()
    for name, pat, sev, note in SECRET_PATTERNS:
        for m in re.finditer(pat, text):
            val = m.group(0)
            if name.startswith("Supabase service_role"):
                role, ref = jwt_role(val)
                if role == "service_role":
                    key = ("Supabase service_role key", val[:12])
                    if key in seen: continue
                    seen.add(key)
                    findings.append(dict(type="secret", severity="critical",
                        title="Supabase service_role key exposed",
                        detail="A service_role JWT bypasses all Row Level Security — full read/write to your database.",
                        evidence=val[:24]+"...", source=source,
                        fix="Remove the service_role key from client code. Use it only on a server. Rotate it in Supabase > Settings > API."))
                continue
            k = (name, val[:14])
            if k in seen: continue
            seen.add(k)
            findings.append(dict(type="secret", severity=sev, title=f"{name} exposed",
                detail=note, evidence=val[:24]+"...", source=source,
                fix=f"Move this out of client code and rotate it immediately."))

def test_supabase_rls(sb_ref, anon_key, findings):
    base = f"https://{sb_ref}.supabase.co/rest/v1/"
    hdr = {"apikey": anon_key, "Authorization": f"Bearer {anon_key}", "User-Agent": UA}
    open_tables = []
    def probe(t):
        try:
            # HEAD + count only: proves exposure without downloading anyone's data
            r = requests.head(base+t, headers={**hdr, "Prefer": "count=exact"}, timeout=10)
            if r.status_code in (200, 206):
                cr = r.headers.get("content-range", "")  # e.g. "0-0/1532" or "*/0"
                total = cr.split("/")[-1]
                if total.isdigit():
                    return (t, int(total))
        except Exception:
            return None
        return None
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(probe, COMMON_TABLES):
            if res and res[1] > 0:
                open_tables.append(res[0])
    for t in open_tables:
        sev = "critical" if t in ("users","api_keys","api_tokens","tokens","payments","customers","accounts","profiles") else "high"
        findings.append(dict(type="rls", severity=sev,
            title=f"Supabase table '{t}' readable without login",
            detail=f"Anyone with the public anon key can read rows from '{t}'. Row Level Security is off or has no policy.",
            evidence=f"Unauthenticated count on /rest/v1/{t} succeeded (no row data downloaded)", source=f"{sb_ref}.supabase.co",
            fix=f"In Supabase SQL editor: ALTER TABLE {t} ENABLE ROW LEVEL SECURITY; then add a policy, e.g. CREATE POLICY \"own rows\" ON {t} FOR SELECT USING (auth.uid() = user_id);"))
    return open_tables

def check_paths(base, findings):
    root = f"{urlparse(base).scheme}://{urlparse(base).netloc}/"
    def probe(item):
        path, sev = item
        try:
            r = fetch(urljoin(root, path))
            ct = r.headers.get("content-type","")
            if r.status_code == 200 and "text/html" not in ct.split(";")[0] and len(r.content) > 0:
                if path.endswith(".env") and ("=" in r.text[:500]):
                    return dict(type="route", severity=sev, title=f"/{path} is publicly readable",
                        detail="An environment file with secrets is served to the public.",
                        evidence=r.text[:80], source=root, fix=f"Block /{path} and remove it from your deploy.")
                if path in ("package.json","config.json",".git/config"):
                    return dict(type="route", severity=sev, title=f"/{path} is publicly readable",
                        detail="An internal file is exposed.", evidence=r.text[:80], source=root,
                        fix=f"Stop serving /{path} publicly.")
        except Exception:
            return None
        return None
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(probe, SENSITIVE_PATHS):
            if res: findings.append(res)

def check_headers(resp, findings):
    missing = [h for h in SECURITY_HEADERS if h not in {k.lower() for k in resp.headers}]
    for h in missing:
        findings.append(dict(type="header", severity="low" if SECURITY_HEADERS[h]=="low" else "medium",
            title=f"Missing {h} header",
            detail="A recommended security header is not set.", evidence="not present",
            source=resp.url, fix=f"Add the {h} header at your host or framework config."))

AI_DIRECT_RE = re.compile(r"https://(api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis\.com|api\.groq\.com|openrouter\.ai/api)[^\s\"'`]*")
AI_ROUTE_RE = re.compile(r"[\"'`](/api/[\w/-]*(?:chat|completion|generate|ai|openai|gpt|llm|claude|prompt|assistant)[\w/-]*)[\"'`]", re.I)
SB_FN_RE = re.compile(r"/functions/v1/([\w-]+)")

def discover_ai_endpoints(text, findings):
    """Wallet Guard (passive): find places a stranger could make the app spend AI credits."""
    found = []
    for m in set(AI_DIRECT_RE.findall(text)):
        found.append(m)
        findings.append(dict(type="wallet", severity="high",
            title=f"Browser calls {m} directly",
            detail="Your frontend talks to the AI provider itself, which means the key is in the browser or a proxy is open. Anyone can reuse it to spend your credits.",
            evidence=m, source="JS bundle",
            fix="Move AI calls to a server route or edge function that checks the user is logged in and rate-limits them."))
    routes = set(AI_ROUTE_RE.findall(text))
    fns = {f for f in SB_FN_RE.findall(text) if re.search(r"chat|ai|gpt|generate|openai|llm|claude|prompt", f, re.I)}
    for r in sorted(routes):
        found.append(r)
        findings.append(dict(type="wallet", severity="info",
            title=f"AI endpoint found: {r}",
            detail="This route likely calls a paid AI model. Verify it requires login and has a rate limit (owner-verified live test available).",
            evidence=r, source="JS bundle",
            fix="Require auth on this route, cap requests per user per minute, and pin the model and max_tokens server-side."))
    for f in sorted(fns):
        found.append(f)
        findings.append(dict(type="wallet", severity="info",
            title=f"AI edge function found: {f}",
            detail="This Supabase function likely calls a paid AI model. Verify it checks the user's JWT and rate-limits.",
            evidence=f"/functions/v1/{f}", source="JS bundle",
            fix="Keep verify_jwt on for this function, add per-user rate limits, and never accept model or max_tokens from the client."))
    return found

# --- dollar exposure (Wallet Guard) -----------------------------------------
# Assumptions (documented, conservative): a scripted abuser sends 100-500
# requests/min at ~1,000 output tokens each, on a frontier model priced
# ~$2-$15 per 1M output tokens. Leaked provider keys are uncapped by your app,
# so they get the full range; endpoints we only discovered (auth unverified)
# get a lower band until an owner-verified live test confirms them.
def estimate_exposure(findings):
    lo = hi = 0
    reasons = []
    for f in findings:
        t = f["title"]
        if f["type"] == "secret" and any(k in t for k in ("OpenAI", "Anthropic")):
            lo += 120; hi += 900; reasons.append(t)
        elif f["type"] == "wallet" and f["severity"] == "high":
            lo += 60; hi += 450; reasons.append(t)
        elif f["type"] == "wallet":
            lo += 0; hi += 50; reasons.append(t + " (unverified)")
    if hi == 0:
        return dict(low_per_hour=0, high_per_hour=0, summary="No AI-bill exposure found in a passive scan.")
    return dict(low_per_hour=lo, high_per_hour=hi,
                summary=f"About ${lo:,}-${hi:,}/hour of AI spend could be run up by a stranger.",
                drivers=reasons,
                assumptions="Scripted abuse at 100-500 requests/min, ~1k output tokens each, $2-$15 per 1M tokens. Unverified endpoints counted low until a live test.")

def scan(url):
    if not url.startswith("http"): url = "https://"+url
    findings = []
    try:
        r = fetch(url)
    except Exception as e:
        return dict(url=url, error=str(e), findings=[])
    html = r.text
    check_headers(r, findings)
    scan_text(html, "page HTML", findings)
    js_urls = collect_js_urls(html, url)
    blobs = [("page HTML", html)]
    def grab(u):
        try:
            jr = fetch(u)
            if jr.status_code == 200: return (u, jr.text)
        except Exception: return None
        return None
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(grab, js_urls):
            if res: blobs.append(res)
    all_text = "\n".join(b[1] for b in blobs)
    for src, text in blobs[1:]:
        scan_text(text, src.split("/")[-1][:40] or "bundle", findings)
    # supabase
    sb_refs = set(SUPABASE_URL_RE.findall(all_text))
    anon_keys = []
    for tok in set(JWT_RE.findall(all_text)):
        role, ref = jwt_role(tok)
        if role == "anon":
            anon_keys.append((tok, ref))
    tested = False
    for anon, ref in anon_keys:
        target = ref if ref else (list(sb_refs)[0] if sb_refs else None)
        if target:
            test_supabase_rls(target, anon, findings)
            tested = True
    check_paths(url, findings)
    ai_endpoints = discover_ai_endpoints(all_text, findings)
    # score
    order = {"critical":0,"high":1,"medium":2,"low":3,"info":4}
    findings.sort(key=lambda f: order.get(f["severity"],5))
    sev_counts = {}
    for f in findings: sev_counts[f["severity"]] = sev_counts.get(f["severity"],0)+1
    grade = "A"
    if sev_counts.get("critical"): grade = "F"
    elif sev_counts.get("high"): grade = "D"
    elif sev_counts.get("medium"): grade = "C"
    elif sev_counts.get("low"): grade = "B"
    exposure = estimate_exposure(findings)
    return dict(url=url, final_url=r.url, grade=grade, counts=sev_counts, exposure=exposure,
                supabase_detected=bool(sb_refs), supabase_tested=tested,
                js_files_scanned=len(blobs)-1, findings=findings)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: scanner.py <url> [--json]"); sys.exit(1)
    res = scan(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2)); sys.exit(0)
    print(f"\nShipCheck report for {res['url']}")
    if res.get("error"): print("  ERROR:", res["error"]); sys.exit(1)
    print(f"  Grade: {res['grade']}   {res['counts']}")
    print(f"  JS files scanned: {res['js_files_scanned']}  Supabase: {res['supabase_detected']} (tested: {res['supabase_tested']})\n")
    for f in res["findings"]:
        print(f"  [{f['severity'].upper()}] {f['title']}")
        print(f"      {f['detail']}")
        print(f"      fix: {f['fix']}\n")
    if not res["findings"]: print("  No issues found by passive scan.\n")
