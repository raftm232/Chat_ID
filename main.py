import os
import logging

from flask import Flask, request, abort, jsonify
import telebot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("telegram-id-bot")

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")
if not WEBHOOK_SECRET:
    raise RuntimeError("Missing WEBHOOK_SECRET environment variable")
if not PUBLIC_URL.startswith("https://"):
    raise RuntimeError("Set PUBLIC_URL to your public HTTPS service URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


@bot.message_handler(commands=["start"])
def start(message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "لا يوجد Username"
    full_name = " ".join(
        part for part in (user.first_name, user.last_name) if part
    ) or "غير معروف"

    bot.reply_to(
        message,
        "👋 أهلاً بيك في بوت معلومات حسابك!\n\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"👤 Username: {username}\n"
        f"📝 الاسم: {full_name}\n\n"
        "🔒 دي البيانات المتاحة للبوت من تليجرام.",
    )


@app.get("/")
def health():
    return {"status": "ok", "bot": "telegram-id-bot"}, 200


@app.post("/webhook")
def webhook():
    supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if supplied_secret != WEBHOOK_SECRET:
        abort(403)

    try:
        update = telebot.types.Update.de_json(request.get_data(as_text=True))
        bot.process_new_updates([update])
        return {"ok": True}, 200
    except Exception:
        log.exception("Failed to process Telegram update")
        return {"ok": False}, 500


def configure_webhook():
    """Register the webhook with Telegram. Never raises (serverless-safe)."""
    webhook_url = f"{PUBLIC_URL}/webhook"
    try:
        bot.set_webhook(url=webhook_url, secret_token=WEBHOOK_SECRET)
        log.info("Webhook configured for %s", webhook_url)
        return True
    except Exception:
        log.exception("Could not configure webhook for %s", webhook_url)
        return False


# --- Serverless-safe auto setup -------------------------------------------
# On Vercel this module is re-imported on cold starts. Calling set_webhook on
# every cold start is wasteful, so we only do it when explicitly requested via
# the AUTO_SET_WEBHOOK env var (set it to "1" for the first deploy, then remove
# it). You can always re-register manually through GET /setup?key=...
if os.environ.get("AUTO_SET_WEBHOOK", "0") == "1":
    configure_webhook()


@app.get("/setup")
def setup():
    """Manual webhook (re)registration, protected by WEBHOOK_SECRET."""
    if request.args.get("key", "") != WEBHOOK_SECRET:
        abort(403)
    ok = configure_webhook()
    return jsonify({"ok": ok, "webhook": f"{PUBLIC_URL}/webhook"}), (
        200 if ok else 500
    )
