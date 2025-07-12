from flask import Flask, request, jsonify, render_template_string, session
import os
import requests
import logging
from dotenv import load_dotenv
import markdown2
from datetime import datetime
import re

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

# Enhanced HTML Template with responsive design
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finance Chatbot</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            padding: 10px;
            overflow: hidden;
        }
        
        .container {
            max-width: 95%;
            width: 100%;
            height: 90vh;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
            position: relative;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="40" r="1.5" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="80" r="1" fill="rgba(255,255,255,0.1)"/></svg>');
        }
        
        .header h1 {
            font-size: 1.5em;
            margin: 0;
            position: relative;
            z-index: 1;
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
        }
        
        .chat-history {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .chat-history::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-history::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        .chat-history::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 10px;
        }
        
        .chat-history::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        .message {
            margin-bottom: 20px;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .user-message {
            display: flex;
            justify-content: flex-end;
            align-items: flex-start;
            gap: 15px;
        }
        
        .bot-message {
            display: flex;
            justify-content: flex-start;
            align-items: flex-start;
            gap: 15px;
        }
        
        .message-bubble {
            max-width: 70%;
            padding: 15px 20px;
            border-radius: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            position: relative;
        }
        
        .user-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .bot-bubble {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
        }
        
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
            flex-shrink: 0;
        }
        
        .user-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .bot-avatar {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
        }
        
        .message-time {
            font-size: 0.8em;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .input-form {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .input-field {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .input-field:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-button {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 1.2em;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .send-button:hover {
            transform: scale(1.1);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .send-button:active {
            transform: scale(0.95);
        }
        
        .clear-button {
            padding: 8px 16px;
            border: 1px solid #dc3545;
            border-radius: 20px;
            background: transparent;
            color: #dc3545;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }
        
        .clear-button:hover {
            background: #dc3545;
            color: white;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        
        .empty-state i {
            font-size: 4em;
            margin-bottom: 20px;
            color: #ddd;
        }
        
        .empty-state h3 {
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        
        .empty-state p {
            font-size: 1.1em;
            opacity: 0.8;
        }
        
        .markdown {
            line-height: 1.6;
        }
        
        .markdown h1, .markdown h2, .markdown h3 {
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .markdown ul, .markdown ol {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        
        .markdown code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        
        .markdown blockquote {
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin: 10px 0;
            color: #555;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            body {
                padding: 5px;
            }
            
            .container {
                border-radius: 15px;
                height: 95vh;
            }
            
            .header {
                padding: 10px 15px;
            }
            
            .header h1 {
                font-size: 1.3em;
            }
            
            .message-bubble {
                max-width: 85%;
            }
            
            .input-area {
                padding: 15px;
            }
            
            .input-field {
                font-size: 16px; /* Prevents zoom on iOS */
            }
        }
        
        @media (max-width: 480px) {
            .header h1 {
                font-size: 1.2em;
            }
            
            .message-bubble {
                max-width: 90%;
                padding: 12px 16px;
            }
            
            .message-avatar {
                width: 35px;
                height: 35px;
                font-size: 1em;
            }
            
            .container {
                height: 98vh;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-chart-line"></i> Finance Chatbot</h1>
        </div>
        
        <div class="chat-container">
            <div class="chat-history" id="chatHistory">
                {% if chat_history and chat_history|length > 0 %}
                    {% for message in chat_history %}
                        {% if message|length >= 3 %}
                            {% set role, content, timestamp = message[0], message[1], message[2] %}
                            <div class="message">
                                {% if role == 'user' %}
                                    <div class="user-message">
                                        <div class="message-bubble user-bubble">
                                            <div>{{ content }}</div>
                                            <div class="message-time">{{ timestamp }}</div>
                                        </div>
                                        <div class="message-avatar user-avatar">
                                            <i class="fas fa-user"></i>
                                        </div>
                                    </div>
                                {% else %}
                                    <div class="bot-message">
                                        <div class="message-avatar bot-avatar">
                                            <i class="fas fa-robot"></i>
                                        </div>
                                        <div class="message-bubble bot-bubble">
                                            <div class="markdown">{{ content | safe }}</div>
                                            <div class="message-time">{{ timestamp }}</div>
                                        </div>
                                    </div>
                                {% endif %}
                            </div>
                        {% endif %}
                    {% endfor %}
                {% else %}
                    <div class="empty-state">
                        <i class="fas fa-comments"></i>
                        <h3>Start a conversation</h3>
                        <p>Ask me anything about finance, investments, or economics!</p>
                    </div>
                {% endif %}
            </div>
            
            <div class="input-area">
                <form method="POST" action="/chat" class="input-form">
                    <input type="text" name="user_input" class="input-field" 
                           placeholder="Ask a financial question..." required autofocus />
                    <button type="submit" class="send-button">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </form>
            </div>
        </div>
    </div>

    <script>
        // Auto-scroll to bottom of chat only for new messages
        let shouldScrollToBottom = true;
        
        function scrollToBottom() {
            const chatHistory = document.getElementById('chatHistory');
            if (shouldScrollToBottom) {
                chatHistory.scrollTop = chatHistory.scrollHeight;
            }
        }
        
        // Check if user has scrolled up
        function checkScroll() {
            const chatHistory = document.getElementById('chatHistory');
            const threshold = 100; // pixels from bottom
            shouldScrollToBottom = (chatHistory.scrollTop + chatHistory.clientHeight + threshold >= chatHistory.scrollHeight);
        }
        
        // Clear chat history
        function clearChat() {
            if (confirm('Are you sure you want to clear the chat history?')) {
                fetch('/clear', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            location.reload();
                        }
                    })
                    .catch(error => {
                        console.error('Error clearing chat:', error);
                        location.reload();
                    });
            }
        }
        
        // Initialize event listeners
        window.addEventListener('load', function() {
            const chatHistory = document.getElementById('chatHistory');
            
            // Add scroll listener to detect if user scrolled up
            chatHistory.addEventListener('scroll', checkScroll);
            
            // Initially scroll to bottom if there are messages
            const messages = chatHistory.querySelectorAll('.message');
            if (messages.length > 0) {
                setTimeout(scrollToBottom, 100);
            }
        });
        
        // Handle form submission
        document.querySelector('form').addEventListener('submit', function(e) {
            // Set flag to scroll to bottom for new messages
            shouldScrollToBottom = true;
            
            // Clear the input field after submission
            setTimeout(function() {
                document.querySelector('.input-field').value = '';
            }, 100);
        });
        
        // Auto-resize input field
        const inputField = document.querySelector('.input-field');
        if (inputField) {
            inputField.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
        }
        
        // Add visual feedback for scroll position
        function updateScrollIndicator() {
            const chatHistory = document.getElementById('chatHistory');
            const isAtBottom = chatHistory.scrollTop + chatHistory.clientHeight >= chatHistory.scrollHeight - 10;
            
            if (!isAtBottom && chatHistory.scrollHeight > chatHistory.clientHeight) {
                if (!document.querySelector('.scroll-indicator')) {
                    const indicator = document.createElement('div');
                    indicator.className = 'scroll-indicator';
                    indicator.innerHTML = '<i class="fas fa-chevron-down"></i>';
                    indicator.style.cssText = `
                        position: absolute;
                        bottom: 80px;
                        right: 30px;
                        background: rgba(102, 126, 234, 0.9);
                        color: white;
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        cursor: pointer;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                        z-index: 1000;
                        animation: bounce 2s infinite;
                    `;
                    indicator.onclick = function() {
                        shouldScrollToBottom = true;
                        scrollToBottom();
                    };
                    document.querySelector('.container').style.position = 'relative';
                    document.querySelector('.container').appendChild(indicator);
                }
            } else {
                const indicator = document.querySelector('.scroll-indicator');
                if (indicator) {
                    indicator.remove();
                }
            }
        }
        
        // Add bounce animation for scroll indicator
        const style = document.createElement('style');
        style.textContent = `
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% {
                    transform: translateY(0);
                }
                40% {
                    transform: translateY(-10px);
                }
                60% {
                    transform: translateY(-5px);
                }
            }
        `;
        document.head.appendChild(style);
        
        // Update scroll indicator on scroll
        document.addEventListener('DOMContentLoaded', function() {
            const chatHistory = document.getElementById('chatHistory');
            if (chatHistory) {
                chatHistory.addEventListener('scroll', updateScrollIndicator);
                setTimeout(updateScrollIndicator, 500);
            }
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template_string(HTML_TEMPLATE, chat_history=session["chat_history"])

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        return render_template_string(HTML_TEMPLATE, chat_history=session.get("chat_history", []))

    # Initialize chat history if not exists
    if "chat_history" not in session:
        session["chat_history"] = []

    # Add timestamp to messages
    timestamp = datetime.now().strftime("%I:%M %p")
    session["chat_history"].append(("user", user_input, timestamp))

    # Prepare messages for AI (only use message content, not timestamps)
    messages = [{"role": "system", "content": "You are a helpful and professional financial assistant. Only answer finance, investment, or economics-related questions. Provide clear, accurate, and helpful information."}]
    
    # Add conversation history (without timestamps for AI)
    for item in session["chat_history"]:
        if len(item) >= 2:  # Ensure we have at least role and content
            role, content = item[0], item[1]
            if role == "user":
                messages.append({"role": "user", "content": content})
            elif role == "bot":
                # Strip HTML tags for AI context
                import re
                clean_content = re.sub('<[^<]+?>', '', content)
                messages.append({"role": "assistant", "content": clean_content})

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
        
        # Convert markdown to HTML
        reply_html = markdown2.markdown(reply)
        
        # Add bot response with timestamp
        bot_timestamp = datetime.now().strftime("%I:%M %p")
        session["chat_history"].append(("bot", reply_html, bot_timestamp))
        
        # Mark session as modified to ensure it's saved
        session.modified = True
        
    except Exception as e:
        logger.error(f"API error: {e}")
        error_msg = "❌ Sorry, something went wrong while getting a response. Please try again."
        error_timestamp = datetime.now().strftime("%I:%M %p")
        session["chat_history"].append(("bot", error_msg, error_timestamp))
        session.modified = True

    return render_template_string(HTML_TEMPLATE, chat_history=session["chat_history"])

@app.route("/clear", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    session.modified = True
    return jsonify({"status": "success"})

if __name__ == "__main__":
    logger.info("Starting Flask app on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
