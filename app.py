import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.environ["BOT_TOKEN"]
PASSWORD = os.environ["BOT_PASSWORD"]

# =========================
# TELEGRAM
# =========================

bot = Bot(token=TOKEN)

app = Flask(__name__)

dispatcher = Dispatcher(bot, None, workers=0)

# Храним авторизованных пользователей
authorized_users = set()

# =========================
# КОМАНДА START
# =========================

def start(update, context):
    user_id = update.effective_user.id

    if user_id in authorized_users:
        update.message.reply_text(
            "😺 Добро пожаловать в Пацюк AI!\n\n"
            "Напиши что угодно 😊"
        )
    else:
        update.message.reply_text(
            "🔒 Бот закрыт.\n\n"
            "Введите пароль:"
        )

# =========================
# ОБРАБОТКА СООБЩЕНИЙ
# =========================

def handle_message(update, context):
    user_id = update.effective_user.id
    text = update.message.text

    # Проверка пароля
    if user_id not in authorized_users:

        if text == PASSWORD:
            authorized_users.add(user_id)

            update.message.reply_text(
                "✅ Доступ разрешён.\n\n"
                "Добро пожаловать в Пацюк AI 😺"
            )

        else:
            update.message.reply_text(
                "❌ Неверный пароль."
            )

        return

    # Ответ бота
    update.message.reply_text(
        f"🐾 Пацюк AI получил сообщение:\n\n{text}"
    )

# =========================
# HANDLERS
# =========================

dispatcher.add_handler(CommandHandler("start", start))

dispatcher.add_handler(
    MessageHandler(
        Filters.text & ~Filters.command,
        handle_message
    )
)

# =========================
# FLASK ROUTES
# =========================

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

@app.route("/", methods=["POST"])
def webhook():

    update = Update.de_json(
        request.get_json(force=True),
        bot
    )

    dispatcher.process_update(update)

    return "ok"

# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
