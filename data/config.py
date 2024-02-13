from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = "5333443423:AAHkeRGfjFwI8BrKDfitWA8a6d76WNxzcdM"  # Bot token

PROJECT_NAME = "aiogramtelegrambot12" # Webhook

WEBHOOK_HOST = f"https://{PROJECT_NAME}.herokuapp.com"
WEBHOOK_PATH = '/webhook/' + BOT_TOKEN
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

ADMINS = [1467352173, 1564519726, 1482922947]  # adminlar ro'yxati