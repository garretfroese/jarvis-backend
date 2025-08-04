# === JARVIS: AI Execution Framework (Autonomous Version) ===

from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

# === EXECUTION FUNCTIONS ===
def create_airtable_base(args):
    name = args.get("name", "Default Base")
    fields = args.get("fields", ["Name", "Email", "Status"])
    return {"status": f"Created Airtable base '{name}' with fields {fields}"}

def send_email(args):
    to = args.get("to")
    subject = args.get("subject")
    body = args.get("body")
    return {"status": f"Sent email to {to} with subject '{subject}'"}

def launch_blog(args):
    name = args.get("name", "New Blog")
    return {"status": f"Launched blog site: {name}"}

# === INTENT-BASED DISPATCHER ===
def execute_intent(intent: str, args: dict):
    if intent == "create_airtable_base":
        return create_airtable_base(args)
    elif intent == "send_email":
        return send_email(args)
    elif intent == "launch_blog":
        return launch_blog(args)
    else:
        return {"status": f"Unknown intent: {intent}"}

# === RELAY ENDPOINT (receives structured command from ChatGPT) ===
@app.route("/relay", methods=["POST"])
def relay():
    secret = request.headers.get("X-JARVIS-KEY")
    expected = os.environ.get("JARVIS_SECRET")

    if not secret or secret != expected:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    intent = data.get("intent")
    args = data.get("args", {})

    result = execute_intent(intent, args)
    return jsonify({"status": "received", "result": result})

# === CHAT ENDPOINT (fallback for user messages) ===
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Missing 'message' in request."}), 400

    # fallback to GPT
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Jarvis, an autonomous AI execution assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        return jsonify({"response": response['choices'][0]['message']['content']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === START ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
