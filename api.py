#!/usr/bin/env python3
"""ShipCheck API: GET / + SEO pages (robots.txt, sitemap.xml, 4 landing pages via seo.py);
POST /api/scan {url} -> report JSON; POST /api/lead {email,url} -> saved.
Stdlib only (no Flask needed) so it runs on any box with python3 + requests.
Run:  python3 api.py  (PORT env, default 8080). Serves index.html at /.
"""
import json, os, re, time, ipaddress, socket, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import scanner
import seo
import urllib.request

# --- Integrations (all optional; each turns on only when its env var is set in Render) ---
POSTHOG_KEY = os.environ.get("POSTHOG_KEY", "")          # PostHog project API key (public, phc_...)
POSTHOG_HOST = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com")
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
RESEND_KEY = os.environ.get("RESEND_API_KEY", "")
LEAD_NOTIFY_TO = os.environ.get("LEAD_NOTIFY_TO", "")    # where new-lead alerts go
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.0, send_default_pii=False)
    except Exception as e:
        print("sentry init failed:", e)

def _post_json(url, payload, headers=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    urllib.request.urlopen(req, timeout=5).read()

def _bg(fn, *a):
    threading.Thread(target=fn, args=a, daemon=True).start()

def track(event, distinct_id, props=None):
    """Server-side PostHog event, fire-and-forget."""
    if not POSTHOG_KEY: return
    def go():
        try: _post_json(POSTHOG_HOST + "/capture/", {"api_key": POSTHOG_KEY, "event": event,
                        "distinct_id": distinct_id or "anon", "properties": props or {}})
        except Exception as e: print("posthog:", e)
    _bg(go)

def notify_lead(email, url):
    """Email André each new lead via Resend so leads survive Render restarts."""
    if not (RESEND_KEY and LEAD_NOTIFY_TO): return
    def go():
        try: _post_json("https://api.resend.com/emails", {
                "from": "ShipCheck <onboarding@resend.dev>", "to": [LEAD_NOTIFY_TO],
                "subject": f"New ShipCheck lead: {email}",
                "text": f"Email: {email}\nScanned URL: {url}\nTime (UTC): {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}"},
                {"Authorization": "Bearer " + RESEND_KEY})
        except Exception as e: print("resend:", e)
    _bg(go)

POSTHOG_SNIPPET = """<script>!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register identify reset get_distinct_id".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);posthog.init("%s",{api_host:"%s",person_profiles:"identified_only",autocapture:false,capture_pageview:true});</script>"""

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
LEADS = os.path.join(HERE, "data", "leads.jsonl")
SCANS = os.path.join(HERE, "data", "scans.jsonl")
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
RATE = {}  # ip -> [timestamps]
LOCK = threading.Lock()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def rate_ok(ip, limit=10, window=3600):
    now = time.time()
    with LOCK:
        hits = [t for t in RATE.get(ip, []) if now - t < window]
        if len(hits) >= limit: RATE[ip] = hits; return False
        hits.append(now); RATE[ip] = hits; return True

def safe_target(url):
    """Block private/internal targets (SSRF guard)."""
    if not url.startswith("http"): url = "https://" + url
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname: return None
    try:
        for info in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved: return None
    except Exception:
        return None
    return url

SEC_HEADERS = (("Strict-Transport-Security", "max-age=31536000"), ("X-Frame-Options", "DENY"),
               ("X-Content-Type-Options", "nosniff"), ("Referrer-Policy", "strict-origin-when-cross-origin"))

class H(SimpleHTTPRequestHandler):
    def _send(self, code, body, ctype, cache=None, head=False):
        if isinstance(body, str): body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        for k, v in SEC_HEADERS: self.send_header(k, v)
        if cache: self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head: self.wfile.write(body)

    def _route(self, head=False):
        # Serve only the landing page, SEO pages and a health check; never the source files.
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path in ("/", "/index.html"):
            body = open(INDEX, "rb").read()
            extra = seo.verification_tags()
            if extra:
                body = body.replace(b"</title>", b"</title>\n    " + extra.encode(), 1)
            if POSTHOG_KEY:
                body = body.replace(b"</head>", (POSTHOG_SNIPPET % (POSTHOG_KEY, POSTHOG_HOST)).encode() + b"</head>", 1)
            return self._send(200, body, "text/html; charset=utf-8", head=head)
        if path == "/robots.txt":
            return self._send(200, seo.robots(), "text/plain; charset=utf-8", "public, max-age=3600", head)
        if path == "/sitemap.xml":
            return self._send(200, seo.sitemap(), "application/xml; charset=utf-8", "public, max-age=3600", head)
        page = seo.render(path.rstrip("/") or "/")
        if page:
            return self._send(200, page, "text/html; charset=utf-8", "public, max-age=3600", head)
        if path == "/healthz":
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "not found"})

    def do_GET(self):
        return self._route()

    def do_HEAD(self):
        # Override the base class so HEAD never maps to files on disk.
        return self._route(head=True)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try: data = json.loads(self.rfile.read(min(n, 10000)) or b"{}")
        except Exception: return self._json(400, {"error": "bad json"})
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        if self.path == "/api/scan":
            if not rate_ok(ip): return self._json(429, {"error": "Too many scans. Try again in an hour."})
            url = safe_target(str(data.get("url", "")).strip())
            if not url: return self._json(400, {"error": "Enter a public URL."})
            host = urlparse(url).hostname
            track("scan_started", ip, {"target_host": host})
            try:
                res = scanner.scan(url)
            except Exception as e:
                if SENTRY_DSN:
                    try: sentry_sdk.capture_exception(e)
                    except Exception: pass
                track("scan_failed", ip, {"target_host": host})
                return self._json(502, {"error": "Scan failed. We've been alerted."})
            track("scan_completed", ip, {"target_host": host, "grade": res.get("grade"), **(res.get("counts") or {})})
            with open(SCANS, "a") as f:
                f.write(json.dumps({"t": time.time(), "url": url, "grade": res.get("grade"), "counts": res.get("counts")}) + "\n")
            return self._json(200, res)
        if self.path == "/api/lead":
            email = str(data.get("email", "")).strip()
            if not EMAIL_RE.match(email): return self._json(400, {"error": "Enter a valid email."})
            with open(LEADS, "a") as f:
                f.write(json.dumps({"t": time.time(), "email": email, "url": data.get("url", "")}) + "\n")
            track("lead_captured", ip, {"target_host": urlparse(str(data.get("url", ""))).hostname})
            notify_lead(email, str(data.get("url", "")))
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"ShipCheck API on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
