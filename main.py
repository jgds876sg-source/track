import discord
from discord.ext import commands
import asyncio
import database
from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    database.init_db()
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")

async def main():
    async with bot:
        # تحميل ملف tracker مباشرة دون استخدام مسار مجلدات
        await bot.load_extension("tracker")
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
