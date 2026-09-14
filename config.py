import os

# جلب توكين البوت من متغيرات بيئة Railway
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# مسار قاعدة البيانات (يقرأ من Railway Volume أو يحفظ محلياً في البيئة التجريبية)
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/roblox_tracker.db")

# الفاصل الزمني للفحص الدوري (بالثواني)
POLLING_INTERVAL = 30
