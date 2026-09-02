import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
with open(SYSTEM_PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "")
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "message field is required"}), 400

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 500
    }

    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=150)
        resp.raise_for_status()
        result = resp.json()
        reply = result["choices"][0]["message"].get("content")
        if not reply:
            reply = "I'm sorry, I had trouble generating a response just now. Could you please rephrase your question?"
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"upstream request failed: {str(e)}"}), 502
    except (KeyError, IndexError):
        return jsonify({"error": "unexpected response format from model"}), 502

    return jsonify({"response": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
