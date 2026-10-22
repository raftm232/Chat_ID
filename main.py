import os
import logging

from flask import Flask, request, abort, jsonify
import telebot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("telegram-id-bot")

TOKEN = os.environ.get("BOT_TOKEN", "").strip()
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").strip()
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")


def config_problems():
    """Return a list of human-readable configuration problems."""
    problems = []
    if not TOKEN:
        problems.append("BOT_TOKEN is missing")
    elif ":" not in TOKEN:
        problems.append("BOT_TOKEN looks wrong: missing ':' between bot id and secret")
    if not WEBHOOK_SECRET:
        problems.append("WEBHOOK_SECRET is missing")
    elif len(WEBHOOK_SECRET) < 16:
        problems.append("WEBHOOK_SECRET is too short (use 32+ chars)")
    if not PUBLIC_URL:
        problems.append("PUBLIC_URL is missing")
    elif not PUBLIC_URL.startswith("https://"):
        problems.append("PUBLIC_URL must start with https://")
    return problems


PROBLEMS = config_problems()

# Never raise at import time on Vercel: an exception there turns into an
# opaque FUNCTION_INVOCATION_FAILED with no useful message. Instead we keep
# the app importable and report the problem through the HTTP responses.
bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)


if bot is not None:

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
    if PROBLEMS:
        return (
            jsonify(
                {
                    "status": "misconfigured",
                    "problems": PROBLEMS,
                    "hint": "Fix these in Vercel -> Settings -> Environment Variables, then Redeploy.",
                }
            ),
            500,
        )
    return {"status": "ok", "bot": "telegram-id-bot"}, 200


@app.post("/webhook")
def webhook():
    if PROBLEMS:
        return jsonify({"ok": False, "problems": PROBLEMS}), 500

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
    """Register the webhook with Telegram. Never raises."""
    if PROBLEMS:
        return False
    webhook_url = f"{PUBLIC_URL}/webhook"
    try:
        bot.set_webhook(url=webhook_url, secret_token=WEBHOOK_SECRET)
        log.info("Webhook configured for %s", webhook_url)
        return True
    except Exception:
        log.exception("Could not configure webhook for %s", webhook_url)
        return False


if os.environ.get("AUTO_SET_WEBHOOK", "0") == "1":
    configure_webhook()


@app.get("/setup")
def setup():
    """Manual webhook (re)registration, protected by WEBHOOK_SECRET."""
    if PROBLEMS:
        return jsonify({"ok": False, "problems": PROBLEMS}), 500
    if request.args.get("key", "") != WEBHOOK_SECRET:
        abort(403)
    ok = configure_webhook()
    return jsonify({"ok": ok, "webhook": f"{PUBLIC_URL}/webhook"}), (
        200 if ok else 500
    )


@app.get("/diag")
def diag():
    """Safe diagnostics: shows which variables are set, never their values."""
    info = {
        "problems": PROBLEMS,
        "BOT_TOKEN_set": bool(TOKEN),
        "BOT_TOKEN_has_colon": ":" in TOKEN,
        "BOT_TOKEN_bot_id": TOKEN.split(":")[0] if ":" in TOKEN else None,
        "WEBHOOK_SECRET_set": bool(WEBHOOK_SECRET),
        "WEBHOOK_SECRET_length": len(WEBHOOK_SECRET),
        "PUBLIC_URL": PUBLIC_URL or None,
        "AUTO_SET_WEBHOOK": os.environ.get("AUTO_SET_WEBHOOK"),
    }
    if bot is not None:
        try:
            me = bot.get_me()
            info["telegram_ok"] = True
            info["bot_username"] = me.username
        except Exception as exc:  # noqa: BLE001
            info["telegram_ok"] = False
            info["telegram_error"] = str(exc)[:200]
    return jsonify(info), 200
