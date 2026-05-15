from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    try:
        message = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
        )

        answer = response.json()["choices"][0]["message"]["content"]

        requests.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": answer[:4000]
            }
        )

    except Exception as e:
        print(e)

    return "ok"

@app.route("/")
def home():
    return "Bot is running!"
