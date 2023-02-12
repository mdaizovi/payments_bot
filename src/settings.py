from decouple import config

SPREADSHEET_NAME = "Telegram Bookings Backend"
EXAMPLE_SHEET_NAME = "TEMPLATE duplicate me!"
ADMIN_USERNAME = "mdaizovi"

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
STRIPE_TOKEN = config('STRIPE_TOKEN')
SECRET_BOT_KEY = config('SECRET_BOT_KEY')

TIMEZONE = "Europe/Berlin"