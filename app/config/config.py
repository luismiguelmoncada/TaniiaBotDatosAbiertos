import os
from dotenv import load_dotenv

# Cargar el archivo .env en el entorno
load_dotenv()

WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
BUSINESS_PHONE = os.getenv("BUSINESS_PHONE")
API_VERSION = os.getenv("API_VERSION", "v19.0")
PORT = int(os.getenv("PORT", "3000"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ELASTICSEARCH_API_KEYU = os.getenv("ELASTICSEARCH_API_KEYU")
ELASTICSEARCH_API_KEYP = os.getenv("ELASTICSEARCH_API_KEYP")