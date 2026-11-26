import os
import time
from collections import defaultdict, deque
from threading import Lock

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5").strip()

client = OpenAI(api_key=API_KEY) if API_KEY else None

SYSTEM_INSTRUCTIONS = """
You are CHAMBO AI, a helpful conversational assistant.
Understand and respond in Tamil, Tanglish, English and other supported languages.
Remember the conversation context provided in each request.
Be friendly, accurate, clear and honest.
Never claim you performed an action you did not perform.
"""

requests_by_ip = defaultdict(deque)
rate_lock = Lock()

def is_rate_limited(ip):
    now = time.time()
    with rate_lock:
        bucket = requests_by_ip[ip]

        while bucket and now - bucket[0] > 60:
            bucket.popleft()

        if len(bucket) >= 20:
            return True

        bucket.append(now)
        return False


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({"configured": client is not None})


@app.route("/api/chat", methods=["POST"])
def chat():

    ip = request.remote_addr or "unknown"

    if is_rate_limited(ip):
        return jsonify({"error": "Please wait before sending another message."}), 429

    if client is None:
        return jsonify({
            "error": "AI API key is not configured on the server."
        }), 503

    data = request.get_json(silent=True) or {}
    messages = data.get("messages")

    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Message is required."}), 400

    if len(messages) > 30:
        return jsonify({"error": "Start a new conversation."}), 400

    clean_messages = []

    for item in messages:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role not in ("user", "assistant"):
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content or len(content) > 6000:
            continue

        clean_messages.append({
            "role": role,
            "content": content
        })

    if not clean_messages:
        return jsonify({"error": "Valid message required."}), 400

    if clean_messages[-1]["role"] != "user":
        return jsonify({"error": "Latest message must be from user."}), 400

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_INSTRUCTIONS,
            input=clean_messages
        )

        answer = response.output_text or "Please try again."

        return jsonify({"reply": answer})

    except Exception:
        app.logger.exception("AI request failed")
        return jsonify({
            "error": "AI service unavailable. Check server configuration."
        }), 502


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)