
import os
from flask import Flask, request, abort
import telebot

TOKEN = os.environ["8758334382:AAH9if_6BZD7KWzszn3erQyr6wDSl4uMOn0"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=["start"])
def start(message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "لا يوجد"
    name = " ".join(
        x for x in [user.first_name, user.last_name] if x
    ) or "غير معروف"

    bot.reply_to(
        message,
        f"👋 أهلاً بيك!\n\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Username: {username}\n"
        f"📝 الاسم: {name}"
    )

@app.route("/", methods=["GET"])
def home():
    return "Telegram bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != WEBHOOK_SECRET:
        abort(403)

    update = telebot.types.Update.de_json(
        request.get_data().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200

if os.environ.get("RENDER_EXTERNAL_URL"):
    bot.set_webhook(
        url=os.environ["RENDER_EXTERNAL_URL"] + "/webhook",
        secret_token=WEBHOOK_SECRET
    )
