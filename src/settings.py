from decouple import config

SPREADSHEET_NAME = "Telegram Bookings Backend"
ADMIN_USERNAME = "mdaizovi"

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
STRIPE_TOKEN = config('STRIPE_TOKEN')
CUSTOM_PAYLOAD = config('CUSTOM_PAYLOAD')