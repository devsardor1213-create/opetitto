import os

# Bot tokenini shu yerga kiriting (BotFather'dan olingan)
BOT_TOKEN = "8743319923:AAGEHda2zjCiU78_JxR-uz7CyezrRtnXCWU"

# Admin paneli uchun maxsus parol
ADMIN_PASSWORD = "superadmin123"

# Adminlarning Telegram ID raqamlari
ADMINS = [123456789] 

# MySQL ma'lumotlar bazasi sozlamalari
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_NAME = "fastfood"

# Telegram Web App uchun URL
# Agar Railway'da bo'lsa, avtomatik ravishda Railway domenini oladi
domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if domain:
    WEBAPP_URL = f"https://{domain}"
else:
    WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://eighty-poems-talk.loca.lt")
