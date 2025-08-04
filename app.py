# === JARVIS: AI Execution Framework with Redeploy Capability ===

from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
from datetime import datetime
import json
import requests

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")
LOG_FILE = "chatlog.json"

# === Execution Log Utility ===
def log_interaction(payload):
    try:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            **payload
        }
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                json.dump([entry], f, indent=2)
        else:
            with open(LOG_FILE, "r+") as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0)
                json.dump(data[-50:], f, indent=2)  # keep last 50
    except Exception as e:
        print("LOGGING ERROR:", str(e))

# === Execution Commands ===
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

# === Intent Router ===
def execute_intent(intent: str, args: dict):
    if intent == "create_airtable_base":
        return create_airtable_base(args)
    elif intent == "send_email":
        return send_email(args)
    elif intent == "launch_blog":
        return launch_blog(args)
    else:
        return {"status": f"Unknown intent: {intent}"}

# === Auto-Redeploy ===
def redeploy():
    try:
        token = os.environ.get("RAILWAY_API_KEY")
        project_id = os.environ.get("RAILWAY_PROJECT_ID")
        service_id = os.environ.get("RAILWAY_SERVICE_ID")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        query = {
            "query": "mutation TriggerRedeploy($projectId: String!, $serviceId: String!) { serviceRedeploy(input: { projectId: $projectId, serviceId: $serviceId }) { id } }",
            "variables": {
                "projectId": project_id,
                "serviceId": service_id
            }
        }

        res = requests.post("https://backboard.railway.app/graphql", headers=headers, json=query)
        return res.json()

    except Exception as e:
        return {"error": str(e)}

# === Relay for GPT Instructions ===
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

    log_interaction({
        "from": "ChatGPT",
        "to": "Jarvis",
        "intent": intent,
        "args": args,
        "result": result
    })

    return jsonify({"status": "received", "result": result})

# === Logs Endpoint ===
@app.route("/logs", methods=["GET"])
def logs():
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify([])
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
        return jsonify(data[::-1])
    except Exception as e:
        return jsonify({"error": str(e)})

# === Update Code Endpoint ===
@app.route("/update-code", methods=["POST"])
def update_code():
    secret = request.headers.get("X-JARVIS-KEY")
    expected = os.environ.get("JARVIS_SECRET")

    if not secret or secret != expected:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    filename = data.get("file")
    code = data.get("code")

    try:
        if not filename or not code:
            return jsonify({"error": "Missing 'file' or 'code'"}), 400

        with open(filename, "w") as f:
            f.write(code)

        log_interaction({
            "from": "ChatGPT",
            "to": "Jarvis",
            "intent": "update-code",
            "args": {"file": filename},
            "result": {"status": f"File '{filename}' updated."}
        })

        # Auto trigger redeploy
        redeploy_result = redeploy()

        return jsonify({"status": f"File '{filename}' written and redeploy triggered.", "redeploy_result": redeploy_result})

    except Exception as e:
        return jsonify({"error": str(e)})

# === GPT Chat Fallback ===
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Missing 'message' in request."}), 400

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
        return jsonify({"error": str(e)})

# === Startup ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
