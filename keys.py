import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
NAGA_USERNAME = os.getenv('NAGA_USERNAME')
NAGA_PASSWORD = os.getenv('NAGA_PASSWORD')
