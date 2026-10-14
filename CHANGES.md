# ShipCheck v0.5 — SEO release (2026-10-14)

Copied from drafts/shipcheck-v0.4. Not deployed.

## Files changed
- `index.html` — new `<title>` (60 chars) and meta description (158 chars); canonical, robots, Open Graph and Twitter card tags; JSON-LD `SoftwareApplication` (price 0 USD) and `FAQPage`; FAQ grew from 3 to 6 Q&As (Lovable check, leaked OpenAI key, Supabase RLS, safety + storage, Wallet Guard, builders); footer links to the 4 landing pages (+3 small CSS rules). Inline JS untouched (byte-identical to v0.4).
- `api.py` — imports `seo`; routing moved into `_route()` (query string stripped before matching); new routes `/robots.txt`, `/sitemap.xml`, `/lovable-security-check`, `/supabase-rls-checker`, `/leaked-api-key-checker`, `/bolt-replit-security-check` (trailing slash tolerated); injects `google-site-verification` / `msvalidate.01` meta on `/` when `GSC_VERIFICATION` / `BING_VERIFICATION` env vars are set; `do_HEAD` overridden so HEAD never falls through to SimpleHTTPRequestHandler's file serving; `_json` skips body on HEAD. Scan/lead POST logic unchanged.
- `seo.py` — NEW. Landing-page content + shared inline CSS (matches index.html palette/fonts), robots.txt, sitemap.xml, verification tags. Optional `SITE_URL` env (default https://shipcheck-esfy.onrender.com).
- `README.md` — documents seo.py and the env vars.
- `CHANGES.md` — this file.

Unchanged: `scanner.py`, `render.yaml`, `requirements.txt`, `.gitignore`.

## Deploy notes
- Upload `index.html`, `api.py`, `seo.py`, `README.md` to GitHub main, then Render deploy hook.
- After deploy: add Render env vars GSC_VERIFICATION / BING_VERIFICATION (content value only, not the full tag), verify in Search Console / Bing Webmaster, submit /sitemap.xml.

## Local test results (2026-10-14)
- 200 + correct content-type: `/`, `/?url=…`, `/index.html` (text/html), `/healthz` (application/json), `/robots.txt` (text/plain), `/sitemap.xml` (application/xml), all 4 landing pages (text/html).
- 404 JSON: `/api.py`, `/scanner.py`, `/seo.py`, `/.env`, `/nope`; HEAD `/api.py` → 404.
- Verification meta present on `/` with env vars set, absent without them, never on landing pages.
- `POST /api/scan` carryingthecross.com → grade B, 3 low (missing HSTS, X-Frame-Options, X-Content-Type-Options) — same as v0.4.
- `node --check` on inline JS: OK. All JSON-LD blocks parse; sitemap is valid XML.
- Not done: visual screenshot check (no headless browser available in sandbox).

## Sources for stats on landing pages
- GitGuardian State of Secrets Sprawl 2026: https://www.gitguardian.com/state-of-secrets-sprawl-report-2026 (28,649,024 new secrets in 2025; AI-service secrets 1,275,105, +81% YoY; Claude Code co-authored commits ~2x baseline leak rate)
- Supabase +992% YoY: https://blog.gitguardian.com/ai-secrets-spread-fast/ (and the report PDF)

## Known pre-existing issue (not fixed here)
- index.html links `hark.css` and `hark-hero.css`, which return 404 JSON in production (and locally); CSS vars like `--gutter`, `--tap` they define are therefore undefined on the live site. Present since before v0.5.
- index.html: removed dead hark.css/hark-hero.css links; defined --gutter/--tap in :root.

## v0.6 (2026-10-14)
- Desktop layout: page container capped at 1120px and centered, wider gutters on desktop, section spacing, base resets (box-sizing, margins, font), defined missing --r-pill/--dur-quick/--ease-out. Restores what the removed hark.css used to provide.
