import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters

TOKEN = os.environ["BOT_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
TMDB_API_KEY = os.environ["TMDB_API_KEY"]
PASSWORD = os.environ["BOT_PASSWORD"]

bot = Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot, None, workers=1)

authorized_users = set()


def ask_ai(text):
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
                        "Ты Пацюк AI 😼 — умный Telegram-бот."
                        "Отвечай всегда на русском языке."
                        "Помогай с фильмами, сериалами и обычным общением."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        }
    )

    data = response.json()

    if "choices" not in data:
        return f"Ошибка OpenRouter:\n{data}"

    return data["choices"][0]["message"]["content"]


def search_movie(query):
    url = "https://api.themoviedb.org/3/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "ru-RU"
    }

    response = requests.get(url, params=params).json()

    if not response.get("results"):
        return "Фильм не найден 😿"

    movie = response["results"][0]

    title = movie.get("title", "Без названия")
    overview = movie.get("overview", "Нет описания")
    rating = movie.get("vote_average", "—")

    poster_path = movie.get("poster_path")

    text = f"🎬 {title}\n⭐ Рейтинг: {rating}\n\n{overview}"

    if poster_path:
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        return text, poster_url

    return text, None


def handle_message(update, context):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in authorized_users:
        if text == PASSWORD:
            authorized_users.add(user_id)

            update.message.reply_text(
                "✅ Доступ разрешён.\n\n"
                "Добро пожаловать в Пацюк AI 😼"
            )
        else:
            update.message.reply_text(
                "🔒 Бот закрыт.\n\n"
                "Введите пароль:"
            )
        return

    if text.startswith("/movie"):
        query = text.replace("/movie", "").strip()

        if not query:
            update.message.reply_text(
                "Напиши название фильма после команды 😼"
            )
            return

        result = search_movie(query)

        if isinstance(result, tuple):
            message, poster = result

            bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=poster,
                caption=message
            )
        else:
            update.message.reply_text(result)

        return

    if text.startswith("/recommend"):
        query = text.replace("/recommend", "").strip()

        answer = ask_ai(
            f"Порекомендуй фильмы и сериалы похожие на: {query}"
        )

        update.message.reply_text(answer)

        return

    answer = ask_ai(text)

    update.message.reply_text(answer)


dispatcher.add_handler(
    MessageHandler(Filters.text & ~Filters.command, handle_message)
)


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(
        request.get_json(force=True),
        bot
    )

    dispatcher.process_update(update)

    return "ok"


@app.route("/")
def index():
    return "Пацюк AI работает 😼"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000
    )
