Telegram ID Bot — hosting package

Files:
- main.py: Flask webhook app
- requirements.txt: Python dependencies

Environment variables required:
- BOT_TOKEN: your NEW Telegram bot token from @BotFather
- WEBHOOK_SECRET: random secret string (use letters, numbers, underscore, hyphen; 32+ chars)
- PUBLIC_URL: the public HTTPS URL of your deployed service, without a trailing slash
  Example format: https://your-service.example.com

Build/install command:
  pip install -r requirements.txt

Start command (Linux shell):
  gunicorn --bind 0.0.0.0:${PORT:-8080} main:app

Important:
1. Revoke the token previously shared in chat using @BotFather /revoke, then use the new token only in hosting environment variables.
2. Do not put secrets in source files or share them.
3. This app uses a Telegram webhook. The hosting service must provide a public HTTPS URL and accept inbound POST requests at /webhook.
4. Set PUBLIC_URL to the exact public HTTPS service URL before starting/redeploying.
5. A free hosting plan may sleep, limit usage, or change terms; 24/7 availability is not guaranteed on free plans.
