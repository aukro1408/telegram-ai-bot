from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

AUTHORIZED_USERS = set()
PASSWORD = "paciuk123"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    try:
        message = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]

        # Проверка доступа
        if user_id not in AUTHORIZED_USERS:

            # Если ввёл пароль
            if message == PASSWORD:
                AUTHORIZED_USERS.add(user_id)

                requests.post(
                    f"{TELEGRAM_API}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": "✅ Доступ разрешён.\n\nДобро пожаловать в paciukAI 😼"
                    }
                )

                return "ok"

            # Если пароль неверный
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "🔒 Бот закрыт.\n\nВведите пароль для доступа:"
                }
            )

            return "ok"

        # Запрос к OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-v4-flash:free",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты дружелюбный Telegram AI бот по имени Пацюк. Всегда отвечай только на русском языке. Кратко, понятно и без китайского текста."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
        )

        result = response.json()

        reply = result["choices"][0]["message"]["content"]

        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": reply
            }
        )

    except Exception as e:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": f"Error: {str(e)}"
            }
        )

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
