from flask import Flask, request, jsonify, render_template_string, session
import os
import requests
import logging
from dotenv import load_dotenv
import markdown2

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Read environment variables
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

API_URL = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
HEADERS = {
    "Content-Type": "application/json",
    "api-key": AZURE_OPENAI_API_KEY
}

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_default_secret_key")

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Finance Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f2f2f2; padding: 30px; }
        #chatbox { max-width: 700px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .message { margin-bottom: 10px; padding: 8px; border-radius: 5px; }
        .user { font-weight: bold; background-color: #f0f0f0; }
        .bot { color: #333; background-color: #eaffea; }
        form { margin-top: 20px; display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 4px; border: 1px solid #ccc; }
        button { padding: 10px 20px; border: none; background: #28a745; color: white; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #218838; }
        .markdown { font-size: 14px; }
    </style>
</head>
<body>
    <div id="chatbox">
        <h2>💸 Finance Chatbot</h2>
        <div id="messages">
            {% for role, content in chat_history %}
                <div class="message {{ 'user' if role == 'user' else 'bot' }}">
                    {% if role == 'user' %}
                        🧑‍💼: {{ content }}
                    {% else %}
                        🤖: <div class="markdown">{{ content | safe }}</div>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        <form method="POST" action="/chat">
            <input type="text" name="user_input" placeholder="Ask a financial question..." required autofocus />
            <button type="submit">Send</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    session.setdefault("chat_history", [])
    return render_template_string(HTML_TEMPLATE, chat_history=session["chat_history"])

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        return render_template_string(HTML_TEMPLATE, chat_history=session["chat_history"])

    session["chat_history"].append(("user", user_input))

    messages = [{"role": "system", "content": "You are a helpful and professional financial assistant. Only answer finance, investment, or economics-related questions."}]
    for role, content in session["chat_history"]:
        messages.append({"role": role if role != 'bot' else 'assistant', "content": content})

    payload = {
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        logger.info(f"AI Response: {reply[:100]}")
        reply_html = markdown2.markdown(reply)
        session["chat_history"].append(("bot", reply_html))
    except Exception as e:
        logger.error(f"API error: {e}")
        error_msg = "❌ Sorry, something went wrong while getting a response."
        session["chat_history"].append(("bot", error_msg))

    return render_template_string(HTML_TEMPLATE, chat_history=session["chat_history"])

if __name__ == "__main__":
    logger.info("Starting Flask app on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
