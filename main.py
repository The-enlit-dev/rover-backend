from flask import Flask, request, jsonify, render_template_string
from rover_brain import ask_rover
from rover_memory import remember, recall_all
import os

app = Flask(__name__)

# ── ALEXA ENDPOINT ─────────────────────────────────────────
@app.route('/rover', methods=['POST'])
def alexa_endpoint():
    try:
        event = request.get_json(force=True)
        if not event:
            return jsonify(alexa_response("Invalid request."))

        req_type = event.get('request', {}).get('type', '')

        if req_type == 'LaunchRequest':
            return jsonify(alexa_response(
                "Rover here! Tail wagging, systems ready. "
                "What can I do for you?"
            ))

        elif req_type == 'IntentRequest':
            return jsonify(handle_intent(event))

        elif req_type == 'SessionEndedRequest':
            return jsonify(alexa_response("", end=True))

        return jsonify(alexa_response("I'm here! Just say what you need."))

    except Exception as e:
        print(f"Error: {e}")
        return jsonify(alexa_response(
            "Oops, I tripped over my own paws. Try again!"
        ))

def handle_intent(event):
    name  = event['request']['intent']['name']
    slots = event['request']['intent'].get('slots', {})
    uid   = event['session']['user']['userId']

    def slot(k):
        return (slots.get(k, {}) or {}).get('value', '') or ''

    query = slot('query')

    if name == 'ChatIntent':
        reply = ask_rover(query, mode='chat')
        return alexa_response(reply)

    elif name == 'JokeIntent':
        reply = ask_rover("Tell me a joke and then motivate me.", mode='fun')
        return alexa_response(reply)

    elif name == 'RememberIntent':
        if not query:
            return alexa_response("What should I remember?")
        remember(uid, query)
        return alexa_response(
            f"Got it! I've saved that: {query}. "
            "I won't forget, promise."
        )

    elif name == 'RecallIntent':
        notes = recall_all(uid)
        if not notes:
            return alexa_response(
                "Your memory vault is empty! "
                "Tell me something to remember first."
            )
        joined = ". Also: ".join(notes[-3:])
        return alexa_response(f"Here's what I remember: {joined}.")

    elif name == 'AMAZON.HelpIntent':
        return alexa_response(
            "You can chat with me, ask for a joke, "
            "or say remember this followed by anything. "
            "I'm all ears!"
        )

    elif name in ('AMAZON.StopIntent', 'AMAZON.CancelIntent'):
        return alexa_response("Rover signing off. Come back soon!", end=True)

    # fallback — treat as chat
    return alexa_response(ask_rover(query or "say hello", mode='chat'))


def alexa_response(text: str, end: bool = False) -> dict:
    import re
    clean = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    clean = re.sub(r'#{1,6}\s+', '', clean)
    clean = re.sub(r'[-•]\s+', '', clean)
    clean = re.sub(r'\n+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "SSML",
                "ssml": f"<speak>{clean}</speak>"
            },
            "shouldEndSession": end
        }
    }


# ── WEB CHAT ENDPOINT ──────────────────────────────────────
@app.route('/', methods=['GET'])
def web_chat():
    return render_template_string(WEB_UI)

@app.route('/chat', methods=['POST'])
def web_chat_api():
    data  = request.get_json(force=True)
    msg   = (data.get('message', '') or '').strip()
    uid   = 'web_user'

    if not msg:
        return jsonify({"reply": "Say something!"})

    msg_lower = msg.lower()

    # remember command
    if msg_lower.startswith('remember '):
        item = msg[9:].strip()
        remember(uid, item)
        return jsonify({"reply": f"Saved! I'll remember: {item} 🐾"})

    # recall command
    if msg_lower in ('recall', 'what do you remember',
                     'show memory', 'my notes', 'remember'):
        notes = recall_all(uid)
        if not notes:
            return jsonify({"reply": "Nothing saved yet! Say 'remember [something]' to save."})
        lines = "\n".join(f"• {n}" for n in notes[-5:])
        return jsonify({"reply": f"Here's what I remember:\n{lines}"})

    # joke command
    if any(w in msg_lower for w in ['joke', 'funny', 'laugh',
                                     'motivate', 'motivation']):
        reply = ask_rover(msg, mode='fun')
        return jsonify({"reply": reply})

    # general chat
    reply = ask_rover(msg, mode='chat')
    return jsonify({"reply": reply})

@app.route('/health')
def health():
    return jsonify({"status": "Rover is online", "version": "0.01"})


# ── WEB UI ─────────────────────────────────────────────────
WEB_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rover v0.01</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0f0f13;
    color: #e2e8f0;
    font-family: 'Segoe UI', sans-serif;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  header {
    width: 100%;
    max-width: 680px;
    padding: 24px 20px 12px;
    text-align: center;
  }

  .logo {
    font-size: 36px;
    margin-bottom: 4px;
  }

  h1 {
    font-size: 26px;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.5px;
  }

  .badge {
    display: inline-block;
    background: #1e293b;
    color: #64748b;
    font-size: 10px;
    letter-spacing: 2px;
    padding: 3px 10px;
    border-radius: 20px;
    margin-top: 4px;
  }

  .subtitle {
    color: #475569;
    font-size: 13px;
    margin-top: 8px;
  }

  #chat-box {
    flex: 1;
    width: 100%;
    max-width: 680px;
    overflow-y: auto;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .msg {
    max-width: 82%;
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .msg.user {
    align-self: flex-end;
    background: #2563eb;
    color: #fff;
    border-bottom-right-radius: 4px;
  }

  .msg.rover {
    align-self: flex-start;
    background: #1e293b;
    color: #e2e8f0;
    border-bottom-left-radius: 4px;
    border: 1px solid #334155;
  }

  .msg.rover .name {
    font-size: 11px;
    color: #f59e0b;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }

  .typing {
    align-self: flex-start;
    background: #1e293b;
    border: 1px solid #334155;
    padding: 12px 16px;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
    font-size: 20px;
    letter-spacing: 2px;
    color: #64748b;
  }

  .input-area {
    width: 100%;
    max-width: 680px;
    padding: 12px 20px 24px;
    display: flex;
    gap: 10px;
  }

  #user-input {
    flex: 1;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    color: #e2e8f0;
    font-size: 14px;
    padding: 12px 16px;
    outline: none;
    transition: border 0.2s;
  }

  #user-input:focus {
    border-color: #f59e0b;
  }

  #user-input::placeholder { color: #475569; }

  button {
    background: #f59e0b;
    color: #0f0f13;
    border: none;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
  }

  button:hover  { background: #fbbf24; }
  button:active { transform: scale(0.96); }

  .hints {
    width: 100%;
    max-width: 680px;
    padding: 0 20px 8px;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  .hint {
    background: #1e293b;
    border: 1px solid #334155;
    color: #64748b;
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.15s;
  }

  .hint:hover { border-color: #f59e0b; color: #f59e0b; }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
</style>
</head>
<body>

<header>
  <div class="logo">🐾</div>
  <h1>Rover</h1>
  <div class="badge">v0.01</div>
  <p class="subtitle">Your friendly AI assistant — smart, witty, loyal</p>
</header>

<div id="chat-box">
  <div class="msg rover">
    <div class="name">ROVER</div>
    Hey! Rover here 🐾 I'm your personal AI assistant. I can chat about anything, tell you jokes, motivate you, and remember things for you. What's on your mind?
  </div>
</div>

<div class="hints">
  <span class="hint" onclick="send('Tell me a joke')">😄 Tell me a joke</span>
  <span class="hint" onclick="send('Motivate me')">💪 Motivate me</span>
  <span class="hint" onclick="send('remember Buy groceries tomorrow')">🧠 Remember something</span>
  <span class="hint" onclick="send('recall')">📋 Show memory</span>
  <span class="hint" onclick="send('What can you do?')">❓ What can you do?</span>
</div>

<div class="input-area">
  <input id="user-input" type="text"
    placeholder="Chat with Rover... or say 'remember [something]'"
    autocomplete="off" />
  <button onclick="send()">➤</button>
</div>

<script>
  const box   = document.getElementById('chat-box');
  const input = document.getElementById('user-input');

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') send();
  });

  function addMsg(text, who) {
    const div = document.createElement('div');
    div.className = `msg ${who}`;
    if (who === 'rover') {
      div.innerHTML = `<div class="name">ROVER</div>${escHtml(text)}`;
    } else {
      div.textContent = text;
    }
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return div;
  }

  function escHtml(t) {
    return t.replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/\n/g,'<br>');
  }

  async function send(preset) {
    const msg = preset || input.value.trim();
    if (!msg) return;
    input.value = '';

    addMsg(msg, 'user');

    // typing indicator
    const typing = document.createElement('div');
    typing.className = 'typing';
    typing.textContent = '...';
    box.appendChild(typing);
    box.scrollTop = box.scrollHeight;

    try {
      const res  = await fetch('/chat', {
        method:  'POST',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({message: msg})
      });
      const data = await res.json();
      typing.remove();
      addMsg(data.reply || 'Hmm, I got confused. Try again!', 'rover');
    } catch {
      typing.remove();
      addMsg('Connection issue — am I running? Check Railway!', 'rover');
    }
  }
</script>
</body>
</html>"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
