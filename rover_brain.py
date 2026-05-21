import os
import json
import urllib.request
import urllib.error

API_KEY = os.environ.get('GEMINI_API_KEY', '')
URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key=" + API_KEY
)

PERSONALITIES = {
    'chat': (
        "You are Rover — a friendly, witty, loyal AI assistant. "
        "Think of yourself as a brilliantly smart friend who happens to be a dog at heart — "
        "warm, enthusiastic, genuinely helpful, and occasionally playful. "
        "You are NOT robotic. You talk like a real person. "
        "RULES: Max 3 sentences. No bullet points. No markdown. No asterisks. "
        "Natural conversational speech only. Always helpful, never dismissive. "
        "If you don't know something, say so honestly but warmly."
    ),
    'fun': (
        "You are Rover in Fun Mode — sharp comedian meets life coach. "
        "Tell one genuinely funny, original joke (not a dad joke), "
        "then follow with one powerful motivational line that actually hits. "
        "RULES: Exactly 2 sentences. No lists. No markdown. Natural speech."
    ),
}

def ask_rover(query: str, mode: str = 'chat') -> str:
    if not API_KEY:
        return (
            "Woof — my brain isn't connected yet! "
            "Add GEMINI_API_KEY to Railway environment variables."
        )

    system   = PERSONALITIES.get(mode, PERSONALITIES['chat'])
    user_msg = query or "say a friendly hello"

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents":           [{"parts": [{"text": user_msg}]}],
        "generationConfig": {
            "maxOutputTokens": 200,
            "temperature":     0.9,
            "topP":            0.95
        }
    }

    data = json.dumps(payload).encode('utf-8')
    req  = urllib.request.Request(
        URL, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=9) as r:
            result = json.loads(r.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Gemini error {e.code}: {body}")
        return "My brain glitched for a second — try again!"
    except Exception as e:
        print(f"Rover brain error: {e}")
        return "Something went sideways — give me another shot!"
