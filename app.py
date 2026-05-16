from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

AUTHORIZED_USERS = set()
PASSWORD = "paciuk123"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text[:4000]
        }
    )


def send_photo(chat_id, photo, caption):
    requests.post(
        f"{TELEGRAM_API}/sendPhoto",
        json={
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption[:1000]
        }
    )


def search_movie(query):

    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "ru-RU"
        }
    )

    data = response.json()

    if not data.get("results"):
        return None

    return data["results"][0]


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

        # Авторизация
        if user_id not in AUTHORIZED_USERS:

            if message == PASSWORD:

                AUTHORIZED_USERS.add(user_id)

                send_message(
                    chat_id,
                    "✅ Доступ разрешён.\n\nДобро пожаловать в Пацюк AI 😼"
                )

                return "ok"

            send_message(
                chat_id,
                "🔒 Бот закрыт.\n\nВведите пароль:"
            )

            return "ok"

        lower = message.lower()

        # ===== ПОИСК ФИЛЬМА =====
        if lower.startswith("/movie "):

            query = message.replace("/movie ", "")

            movie = search_movie(query)

            if not movie:
                send_message(chat_id, "Фильм не найден 😿")
                return "ok"

            title = movie.get("title", "Без названия")
            overview = movie.get("overview", "Нет описания")
            rating = movie.get("vote_average", "?")
            date = movie.get("release_date", "")
            poster = movie.get("poster_path")

            text = (
                f"🎬 {title}\n\n"
                f"⭐ Рейтинг: {rating}\n"
                f"📅 Год: {date[:4]}\n\n"
                f"{overview}"
            )

            if poster:

                photo_url = f"https://image.tmdb.org/t/p/w500{poster}"

                send_photo(chat_id, photo_url, text)

            else:
                send_message(chat_id, text)

            return "ok"

        # ===== AI РЕКОМЕНДАЦИИ =====
        if lower.startswith("/recommend"):

            prompt = (
                "Порекомендуй фильмы.\n"
                f"Запрос пользователя: {message}"
            )

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek/deepseek-v4-flash:free",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Ты эксперт по фильмам. "
                                "Отвечай только на русском языке."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )

            result = response.json()

            if "choices" in result:
                answer = result["choices"][0]["message"]["content"]
            else:
                answer = str(result)

            send_message(chat_id, answer)

            return "ok"

        # ===== ОБЫЧНЫЙ AI ЧАТ =====
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-v4-flash:free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты дружелюбный AI кот по имени Пацюк. "
                            "Всегда отвечай только на русском языке."
                        )
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
        )

        result = response.json()

        if "choices" in result:
            answer = result["choices"][0]["message"]["content"]
        else:
            answer = str(result)

        send_message(chat_id, answer)

    except Exception as e:

        send_message(
            chat_id,
            f"Ошибка 😿\n{str(e)}"
        )

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
