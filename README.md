# ShipCheck
Can a stranger make your AI app spend your money? Free passive security scan for vibe-coded apps (Lovable, Bolt, Replit, Cursor, v0).
- `scanner.py` — the scan engine (leaked keys, Supabase RLS exposure via count-only checks, exposed files, AI endpoints, headers, $ exposure estimate)
- `api.py` — stdlib web server: `GET /` landing page, `POST /api/scan`, `POST /api/lead`, `GET /healthz`
Run locally: `pip install -r requirements.txt && python3 api.py`
