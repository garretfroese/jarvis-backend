# === Jarvis Backend with Command Execution ===

from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

# === Action Handlers ===
def create_crm():
    # Placeholder for CRM creation logic (e.g. create Airtable base via API)
    return {"status": "CRM created successfully."}

def send_email():
    # Placeholder for email-sending logic (e.g. use Gmail API)
    return {"status": "Email sent successfully."}

def launch_blog():
    # Placeholder for deploying a simple blog (e.g. via GitHub Pages or Railway)
    return {"status": "Blog launched successfully."}

# === Command Router ===
def route_command(command: str, args: dict = {}):
    command = command.lower()

    if "create crm" in command:
        return create_crm(args)
    elif "send email" in command:
        return send_email(args)
    elif "launch blog" in command:
        return launch_blog(args)
    else:
        return {"status": f"Unknown command: {command}"}


# === GPT Chat Endpoint ===
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Missing 'message' in request."}), 400

    # Route known commands first
    routed = route_command(user_message)
    if routed:
        return jsonify({"response": f"✅ Executed: {routed['status']}"})

    # Fallback to GPT-4 chat
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Jarvis, an AI assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        return jsonify({"response": response['choices'][0]['message']['content']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, request, jsonify
import os

# Add this route
@app.route("/relay", methods=["POST"])
def relay():
    secret = request.headers.get("X-JARVIS-KEY")
    expected = os.environ.get("JARVIS_SECRET")

    if not secret or secret != expected:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    command = data.get("command", "")
    args = data.get("args", {})

    result = route_command(command, args)
    return jsonify({"status": "received", "result": result})
