"""ShipCheck SEO: robots.txt, sitemap.xml, and server-rendered landing pages.
Stdlib only. Imported by api.py. Content is static HTML; no JS needed.
"""
import html, json, os

SITE = os.environ.get("SITE_URL", "https://shipcheck-esfy.onrender.com").rstrip("/")
LASTMOD = "2026-10-14"

GG_REPORT = "https://www.gitguardian.com/state-of-secrets-sprawl-report-2026"
GG_BLOG = "https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026"
GG_SUPA = "https://blog.gitguardian.com/ai-secrets-spread-fast/"

STYLE = """
:root{color-scheme:dark;--bg:#0b0d10;--bg2:#12151a;--bg3:#191d23;--line:#ffffff14;--line2:#ffffff24;--text:#eef1f4;--muted:#9aa3ad;--lime:#c6ff3d;--ink:#0b0d10;
--mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
*{box-sizing:border-box}html,body{margin:0}body{background:var(--bg);color:var(--text);font:400 17px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
::selection{background:var(--lime);color:var(--ink)}a{color:var(--lime)}
.bar{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 20px;background:#0b0d10cc;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}
.logo{display:inline-flex;align-items:center;gap:8px;font-weight:700;font-size:17px;letter-spacing:-.02em;color:var(--text);text-decoration:none;min-height:44px}.logo svg{color:var(--lime)}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 18px;border-radius:12px;border:1px solid var(--line2);background:var(--bg3);color:var(--text);font:600 15px/1 var(--sans);text-decoration:none;cursor:pointer}
.btn--lime{background:var(--lime);color:var(--ink);border-color:var(--lime)}.btn--lime:hover{filter:brightness(1.05)}
main{max-width:760px;margin:0 auto;padding:40px 20px 24px}
.eyebrow{font:500 12px/1.3 var(--mono);color:var(--lime);letter-spacing:.08em;text-transform:uppercase;margin:0}
h1{font-size:clamp(32px,6vw,50px);line-height:1.06;letter-spacing:-.035em;margin:10px 0 14px}
h2{font-size:clamp(23px,4vw,30px);line-height:1.15;letter-spacing:-.025em;margin:40px 0 10px}
h3{font-size:18px;margin:22px 0 4px}
p,li{color:#cfd5db}.lede{font-size:19px;color:var(--text)}
ul,ol{padding-left:22px}li{margin:6px 0}
code{font:400 14px/1.4 var(--mono);background:var(--bg3);border:1px solid var(--line);border-radius:6px;padding:1px 6px;color:var(--text)}
pre{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;overflow-x:auto}pre code{background:none;border:0;padding:0}
.scan{display:grid;gap:10px;padding:8px;margin:22px 0 6px;border-radius:18px;background:var(--bg2);border:1px solid var(--line2)}
.scan:focus-within{border-color:#c6ff3d80}
.scan input{min-width:0;height:52px;padding:0 14px;border:0;outline:0;border-radius:12px;background:var(--bg);color:var(--text);font:400 16px/1 var(--mono)}
.scan .btn{min-height:52px;font-size:16px}@media(min-width:640px){.scan{grid-template-columns:1fr auto}}
.note{font-size:14px;color:var(--muted);margin:0}
.stats{display:grid;gap:12px;margin:18px 0}@media(min-width:640px){.stats{grid-template-columns:repeat(3,1fr)}}
.stat{padding:16px;border-radius:16px;background:var(--bg2);border:1px solid var(--line)}
.stat b{display:block;font-size:26px;letter-spacing:-.03em;color:var(--text)}.stat span{font-size:14px;color:var(--muted);line-height:1.4;display:block}
.cta{margin-top:48px;padding:32px 20px;text-align:center;border-radius:22px;border:1px solid var(--line2);background:radial-gradient(closest-side,#c6ff3d1f,transparent),var(--bg2)}
.cta h2{margin-top:0}
.src{font-size:14px;color:var(--muted)}
.related{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.related a{font-size:14px;padding:8px 12px;border-radius:10px;border:1px solid var(--line2);text-decoration:none;color:var(--text)}
footer{max-width:760px;margin:0 auto;padding:24px 20px 48px;color:var(--muted);font-size:14px;border-top:1px solid var(--line)}
"""

LOGO = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 2.5 4 5.5v6c0 5 3.4 8.8 8 10 4.6-1.2 8-5 8-10v-6l-8-3Z" '
        'stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="m8.5 12 2.5 2.5 4.5-5" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>')

def scan_form(placeholder="https://your-app.lovable.app", label="Scan my app — free"):
    return (f'<form class="scan" action="/" method="get">'
            f'<input name="url" type="url" inputmode="url" autocomplete="url" autocapitalize="off" spellcheck="false" '
            f'aria-label="Your app\'s URL" placeholder="{html.escape(placeholder)}" required>'
            f'<button class="btn btn--lime" type="submit">{html.escape(label)}</button></form>'
            '<p class="note">Passive scan. We only read what any browser can see. No signup. Free.</p>')

GG_STATS = (f'<div class="stats">'
            f'<div class="stat"><b>28.65M</b><span>new secrets leaked in public GitHub commits in 2025</span></div>'
            f'<div class="stat"><b>+81%</b><span>AI-service secrets, up to 1,275,105 in a year</span></div>'
            f'<div class="stat"><b>+992%</b><span>growth in leaked Supabase secrets year over year</span></div>'
            f'</div><p class="src">Source: <a href="{GG_REPORT}" rel="noopener">GitGuardian, State of Secrets Sprawl 2026</a>.</p>')

PAGES = {}

def page(slug, title, description, h1, eyebrow, body, placeholder="https://your-app.lovable.app"):
    PAGES["/" + slug] = dict(title=title, description=description, h1=h1, eyebrow=eyebrow, body=body, placeholder=placeholder)

# ---------------------------------------------------------------- /lovable-security-check
page("lovable-security-check",
     "Lovable Security Check: Scan Your App for Leaks | ShipCheck",
     "Free security check for Lovable apps. Find leaked API keys in your bundle, Supabase tables readable without RLS, exposed files and AI endpoints that can run up your bill.",
     "Check your Lovable app for security issues",
     "Lovable security check",
     f"""
<p class="lede">Lovable gets you from prompt to live app in an afternoon. The parts it moves fast past, like where secrets live and who can read your database, are where most of the problems show up. Paste your <code>.lovable.app</code> URL or custom domain and ShipCheck shows you what a stranger can see.</p>
{{FORM}}
<h2>What usually goes wrong in a Lovable app</h2>
<h3>1. Row Level Security is off, or too loose</h3>
<p>Lovable apps typically use Supabase as the backend. The Supabase URL and anon (publishable) key ship in your JavaScript; that is by design. What protects your data is Row Level Security. If a table has RLS disabled, or a policy like <code>using (true)</code>, anyone who copies the anon key from your bundle can read that table straight from the Supabase REST API. This is the class of issue behind CVE-2025-48757, which exposed data across many Lovable-built apps.</p>
<h3>2. A secret key ended up in the frontend</h3>
<p>Asking the AI to "call OpenAI" or "add Stripe" can land a secret key in client code. Anything in the browser bundle is public, even if it is minified. The worst cases are a Supabase <code>service_role</code> or <code>sb_secret_</code> key, which bypasses RLS entirely, and LLM keys (OpenAI, Anthropic, OpenRouter, DeepSeek), which let anyone spend your credits.</p>
<h3>3. AI endpoints anyone can call</h3>
<p>An edge function that forwards prompts to a model, with no auth check and no rate limit, is a free AI API for whoever finds it. ShipCheck's Wallet Guard flags endpoints like this and estimates what scripted abuse could cost per hour.</p>
<h3>4. Missing security headers</h3>
<p>No Content-Security-Policy, no clickjacking protection. Lower risk, but cheap to fix once you know.</p>

<h2>Why this matters now</h2>
{{STATS}}
<p>Leaked Supabase secrets are growing faster than almost any other category. GitGuardian links the jump to new developers reaching for plug-and-play backends through AI-assisted coding, which describes most Lovable projects.</p>

<h2>How to fix what the scan finds</h2>
<ol>
<li><b>Turn on RLS for every table</b> in the Supabase dashboard (Table Editor → table → Enable RLS), then add policies that tie rows to <code>auth.uid()</code>. A table with RLS on and no policies is locked to the anon key, which is a safe default.</li>
<li><b>Move secret keys server-side.</b> Put them in Supabase Edge Function secrets and call the provider from the function, never from the browser.</li>
<li><b>Rotate anything that leaked.</b> Deleting the key from code is not enough; it is already in your deployed bundle and possibly in git history. Revoke it at the provider and issue a new one.</li>
<li><b>Require auth and add limits on AI routes</b>: check the user's session in the function, cap requests per user, and set a spend limit in your model provider's dashboard.</li>
<li><b>Re-scan after you redeploy</b> to confirm the fix shipped.</li>
</ol>
<p>If you use Lovable's own built-in security scan, keep using it; a second, outside look at the live site catches what is actually deployed.</p>
""")

# ---------------------------------------------------------------- /supabase-rls-checker
page("supabase-rls-checker",
     "Supabase RLS Checker: Find Tables Open Without RLS | ShipCheck",
     "Free Supabase RLS checker. See which tables in your live app can be read with the public anon key, spot leaked service_role keys, and get the SQL to fix it.",
     "Supabase RLS checker",
     "Supabase security",
     f"""
<p class="lede">Your Supabase anon key is public. Every visitor's browser has it. The only thing between that key and your data is Row Level Security. ShipCheck finds the Supabase project your app talks to and tests whether common tables answer anonymous requests.</p>
{{FORM}}
<h2>How the check works</h2>
<p>ShipCheck reads your app's public JavaScript, pulls out the Supabase project URL and anon key, then sends a <b>count-only</b> request (<code>HEAD</code> with <code>Prefer: count=exact</code>) to the REST API for tables apps commonly create: <code>users</code>, <code>profiles</code>, <code>orders</code>, <code>payments</code>, <code>messages</code>, <code>api_keys</code> and others. If the count comes back, the table is readable by anyone. No row data is downloaded. It also decodes any JWT it finds to tell you whether a <code>service_role</code> key is sitting in your frontend, and flags new-format <code>sb_secret_</code> keys.</p>
<p>Because it only guesses common table names, a clean result is not proof that every table is safe. Treat it as a fast first pass and confirm in the dashboard.</p>

<h2>What goes wrong</h2>
<ul>
<li><b>RLS never enabled.</b> Tables created through SQL or migrations may not have RLS turned on, and some quick-start flows leave it off.</li>
<li><b>Policies that allow everything.</b> A <code>select</code> policy with <code>using (true)</code> for the <code>anon</code> role is the same as no RLS for reads.</li>
<li><b>Read is locked, write is not.</b> Insert or update policies without a <code>with check</code> let anyone write rows.</li>
<li><b>service_role in the browser.</b> This key bypasses RLS completely. If it is in your bundle, policies do not matter.</li>
</ul>

<h2>How to fix it</h2>
<p>Enable RLS, then grant only what each user should see:</p>
<pre><code>alter table public.profiles enable row level security;

create policy "Users read own profile"
  on public.profiles for select
  to authenticated
  using ( (select auth.uid()) = id );

create policy "Users update own profile"
  on public.profiles for update
  to authenticated
  using ( (select auth.uid()) = id )
  with check ( (select auth.uid()) = id );</code></pre>
<p>Then check the rest of the project:</p>
<ol>
<li>Open the Supabase dashboard's Security Advisor; it lists tables in exposed schemas with RLS disabled.</li>
<li>If a <code>service_role</code> or <code>sb_secret_</code> key leaked, rotate it in Project Settings → API Keys and move any code that needs it into an Edge Function or server.</li>
<li>Re-run ShipCheck on the live URL after you deploy.</li>
</ol>

<h2>Why Supabase keys are a growing target</h2>
{{STATS}}
<p>GitGuardian reports that Supabase now ranks among the 20 most-leaked secret types, a side effect of how many AI-built apps use it as their default backend (<a href="{GG_SUPA}" rel="noopener">GitGuardian blog</a>).</p>
""", placeholder="https://your-app.com")

# ---------------------------------------------------------------- /leaked-api-key-checker
page("leaked-api-key-checker",
     "Leaked API Key Checker for OpenAI, Stripe & More | ShipCheck",
     "Free leaked API key checker. Scan your live site's JavaScript for exposed OpenAI, Anthropic, OpenRouter, DeepSeek, Stripe, AWS, GitHub and Supabase keys before someone else does.",
     "Leaked API key checker",
     "Leaked keys",
     f"""
<p class="lede">If a secret key is in your frontend, it is public. Minifying does not hide it, and neither does a <code>.env</code> file if your build tool inlines it. ShipCheck downloads the same HTML and JavaScript a visitor gets and searches it for live-looking keys.</p>
{{FORM}}
<h2>The keys ShipCheck looks for</h2>
<ul>
<li><b>LLM providers:</b> OpenAI (<code>sk-proj-</code>, <code>sk-</code>), Anthropic (<code>sk-ant-</code>), OpenRouter (<code>sk-or-v1-</code>), DeepSeek, xAI (<code>xai-</code>), Groq (<code>gsk_</code>), Perplexity (<code>pplx-</code>), Hugging Face (<code>hf_</code>).</li>
<li><b>AI tooling:</b> Firecrawl (<code>fc-</code>).</li>
<li><b>Payments and cloud:</b> Stripe secret keys (<code>sk_live_</code>), AWS access keys (<code>AKIA…</code>), GitHub tokens (<code>ghp_</code>, <code>github_pat_</code>).</li>
<li><b>Databases:</b> Supabase <code>service_role</code> JWTs and <code>sb_secret_</code> keys, plus Postgres and MongoDB connection strings with credentials.</li>
</ul>
<p>Findings show a truncated preview of the key, never the full value, and are sorted by severity.</p>

<h2>Why AI keys leak so often</h2>
{{STATS}}
<p>GitGuardian found that keys for AI services grew faster than any other category in 2025, with OpenRouter and DeepSeek among the fastest risers (<a href="{GG_BLOG}" rel="noopener">GitGuardian</a>). In vibe-coded apps, the usual path is simple: the AI writes a <code>fetch</code> to the model API from the browser and puts the key next to it. With Vite, any variable prefixed <code>VITE_</code> is bundled into client code; with Next.js, anything prefixed <code>NEXT_PUBLIC_</code> is. Those prefixes mean "public", so they should never hold a secret.</p>
<p>A leaked LLM key costs money fast. Scripts scan the web for keys and resell or burn the credits. ShipCheck's Wallet Guard estimates how much an exposed key or open AI endpoint could cost you per hour.</p>

<h2>What to do if a key leaked</h2>
<ol>
<li><b>Revoke it first.</b> Go to the provider's dashboard and delete or roll the key. Removing it from code does not help while the old key still works.</li>
<li><b>Check usage.</b> Look at billing and logs for requests you did not make.</li>
<li><b>Move the call server-side.</b> Use a serverless function, edge function or backend route that holds the key in an environment variable and checks the user's session.</li>
<li><b>Set spend limits</b> in the provider dashboard so one leak cannot drain your account.</li>
<li><b>Clean git history</b> if the key was ever committed, and add secret scanning to your repo.</li>
<li><b>Re-scan</b> the live site to confirm the new build no longer ships it.</li>
</ol>
""", placeholder="https://your-app.com")

# ---------------------------------------------------------------- /bolt-replit-security-check
page("bolt-replit-security-check",
     "Bolt & Replit Security Check: Free Scan | ShipCheck",
     "Free security check for apps built with Bolt.new and Replit. Find exposed API keys, open Supabase tables, public .env and .git files, and unprotected AI endpoints.",
     "Security check for Bolt and Replit apps",
     "Bolt & Replit",
     f"""
<p class="lede">Bolt.new and Replit Agent can build and deploy a full-stack app from a prompt. ShipCheck checks the deployed result the way an outsider would: what is in the bundle, what files are reachable, and which APIs answer without a login.</p>
{{FORM}}
<h2>Common problems in Bolt and Replit apps</h2>
<h3>Secrets in client code</h3>
<p>Bolt projects are usually Vite or Next.js frontends. When the agent wires up an AI or payment API directly in a React component, the key ships to every visitor. Replit has a Secrets tool that stores values as environment variables, which is the right place for them, but a secret read in frontend code, or a <code>VITE_</code>-prefixed variable, is still bundled and public.</p>
<h3>Exposed files</h3>
<p>Misconfigured static hosting can serve <code>/.env</code>, <code>/.git/config</code> or <code>config.json</code>. A reachable <code>.env</code> usually means every credential in the project is compromised. ShipCheck probes these paths and only reports a hit when the response looks like the real file.</p>
<h3>Open databases</h3>
<p>Many Bolt apps use Supabase. If Row Level Security is off on a table, the public anon key in your JavaScript is enough to read it. ShipCheck tests common tables with count-only requests and downloads no row data. See the <a href="/supabase-rls-checker">Supabase RLS checker</a> for details.</p>
<h3>AI endpoints with no limits</h3>
<p>A server route that passes prompts to a model with no auth and no rate limit lets anyone use your AI budget. Wallet Guard finds these routes and estimates the hourly cost of abuse.</p>
<h3>Missing headers</h3>
<p>No Content-Security-Policy, HSTS, X-Frame-Options or X-Content-Type-Options. Each is a few lines of config.</p>

<h2>The numbers behind the risk</h2>
{{STATS}}
<p>GitGuardian also found that commits co-authored by Claude Code leaked secrets at roughly twice the baseline rate across public GitHub in 2025. Speed is the point of these tools; a quick check before launch keeps it from costing you.</p>

<h2>How to fix what you find</h2>
<ol>
<li><b>Rotate any exposed key</b> at the provider, then store the new one only in server-side environment variables (Replit Secrets, your Bolt host's env settings, or Supabase Edge Function secrets).</li>
<li><b>Proxy third-party APIs</b> through a backend route that checks the user's session and rate-limits requests.</li>
<li><b>Block dotfiles</b> on your host and make sure <code>.env</code> is in <code>.gitignore</code>.</li>
<li><b>Enable RLS</b> on every Supabase table and write per-user policies.</li>
<li><b>Add security headers</b> in your host's config or middleware.</li>
<li><b>Re-scan</b> after each deploy.</li>
</ol>
""", placeholder="https://your-app.com")

RELATED = [("/lovable-security-check", "Lovable security check"), ("/supabase-rls-checker", "Supabase RLS checker"),
           ("/leaked-api-key-checker", "Leaked API key checker"), ("/bolt-replit-security-check", "Bolt & Replit security check")]

def render(path):
    p = PAGES.get(path)
    if not p: return None
    url = SITE + path
    e = html.escape
    body = p["body"].replace("{FORM}", scan_form(p["placeholder"])).replace("{STATS}", GG_STATS)
    related = "".join(f'<a href="{h}">{e(t)}</a>' for h, t in RELATED if h != path)
    ld = ('{"@context":"https://schema.org","@type":"WebPage","name":%s,"description":%s,"url":%s,'
          '"isPartOf":{"@type":"WebSite","name":"ShipCheck","url":%s}}') % tuple(
              json.dumps(x) for x in (p["title"], p["description"], url, SITE + "/"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(p["title"])}</title>
<meta name="description" content="{e(p["description"])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="article">
<meta property="og:site_name" content="ShipCheck">
<meta property="og:title" content="{e(p["title"])}">
<meta property="og:description" content="{e(p["description"])}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(p["title"])}">
<meta name="twitter:description" content="{e(p["description"])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>{STYLE}</style>
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="bar">
<a class="logo" href="/" aria-label="ShipCheck home">{LOGO}ShipCheck</a>
<a class="btn btn--lime" href="/#scan">Scan free</a>
</header>
<main>
<p class="eyebrow">{e(p["eyebrow"])}</p>
<h1>{e(p["h1"])}</h1>
{body}
<div class="cta">
<h2>Find the leak before a stranger does.</h2>
{scan_form(p["placeholder"])}
</div>
<h2>More free checks</h2>
<div class="related">{related}</div>
</main>
<footer><p><strong>ShipCheck</strong> — free passive security scanner for vibe-coded apps. ShipCheck is not affiliated with Lovable, Bolt, Replit, Supabase or GitGuardian.</p><p>© 2026 ShipCheck</p></footer>
</body>
</html>"""

def robots():
    return f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {SITE}/sitemap.xml\n"

def sitemap():
    urls = ["/"] + list(PAGES)
    items = "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{LASTMOD}</lastmod><priority>{'1.0' if u == '/' else '0.8'}</priority></url>\n" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'

def verification_tags():
    tags = ""
    g = os.environ.get("GSC_VERIFICATION", "").strip()
    b = os.environ.get("BING_VERIFICATION", "").strip()
    if g: tags += f'<meta name="google-site-verification" content="{html.escape(g, quote=True)}" />'
    if b: tags += f'<meta name="msvalidate.01" content="{html.escape(b, quote=True)}" />'
    return tags
