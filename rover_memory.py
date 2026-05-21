import os
import json
import urllib.request
import urllib.parse

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

def _headers():
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal"
    }

def _safe_id(uid: str) -> str:
    return uid.replace(':', '_').replace('.', '_').replace('-', '_')[-40:]

def _req(method: str, table: str, data: dict = None, params: str = ''):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase not configured — memory disabled")
        return []
    url  = f"{SUPABASE_URL}/rest/v1/{table}{params}"
    body = json.dumps(data).encode('utf-8') if data else None
    req  = urllib.request.Request(
        url, data=body, headers=_headers(), method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            text = r.read().decode('utf-8')
            return json.loads(text) if text.strip() else []
    except Exception as e:
        print(f"Memory error: {e}")
        return []

def remember(user_id: str, content: str):
    """Save a note to the vault."""
    uid = _safe_id(user_id)
    _req('POST', 'vault', data={'user_id': uid, 'content': content})

def recall_all(user_id: str, limit: int = 5) -> list:
    """Get recent saved notes."""
    uid  = _safe_id(user_id)
    rows = _req(
        'GET', 'vault',
        params=f'?user_id=eq.{urllib.parse.quote(uid)}'
               f'&order=created_at.desc&limit={limit}&select=content'
    )
    return [r['content'] for r in rows] if rows else []
