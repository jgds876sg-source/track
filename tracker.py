import discord
from discord.ext import commands, tasks
import aiohttp
import json
import datetime
import database
from config import POLLING_INTERVAL

class TrackerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracker_loop.start()

    def cog_unload(self):
        self.tracker_loop.cancel()

    async def fetch_json(self, session, url, method="GET", json_data=None):
        try:
            if method == "POST":
                async with session.post(url, json=json_data, timeout=10) as resp:
                    if resp.status == 200: return await resp.json()
            else:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200: return await resp.json()
        except Exception:
            return None
        return None

    async def get_place_name(self, session, place_id):
        u_url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe-id"
        u_data = await self.fetch_json(session, u_url)
        if u_data and 'universeId' in u_data:
            universe_id = u_data['universeId']
            g_url = f"https://games.roblox.com/v1/games?universeIds={universe_id}"
            g_data = await self.fetch_json(session, g_url)
            if g_data and 'data' in g_data and len(g_data['data']) > 0:
                return g_data['data'][0].get('name', f"Place ID: {place_id}")
        return f"Place ID: {place_id}"

    async def get_user_details(self, session, user_id):
        data = await self.fetch_json(session, f"https://users.roblox.com/v1/users/{user_id}")
        if data:
            return data.get('name', f"User_{user_id}"), data.get('displayName', f"User_{user_id}")
        return f"User_{user_id}", f"User_{user_id}"

    @tasks.loop(seconds=POLLING_INTERVAL)
    async def tracker_loop(self):
        users = database.get_all_tracked()
        if not users:
            return

        async with aiohttp.ClientSession() as session:
            for row in users:
                u_id, channel_id, last_pres, last_place, friends_json, k_badges = row
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue

                # 1. مراقبة التواجد والماب بالاسم
                p_data = await self.fetch_json(session, "https://presence.roblox.com/v1/presence/users", "POST", {"userIds": [u_id]})
                if p_data and p_data.get('userPresences'):
                    pres_info = p_data['userPresences'][0]
                    curr_pres = pres_info.get('userPresenceType') # 0: Off, 1: On, 2: InGame
                    curr_place = pres_info.get('placeId')

                    if curr_pres != last_pres or curr_place != last_place:
                        embed = discord.Embed(title="🚨 تحديث حالة اللاعب", color=discord.Color.blue(), timestamp=datetime.datetime.now(datetime.timezone.utc))
                        if curr_pres == 2 and curr_place:
                            map_name = await self.get_place_name(session, curr_place)
                            embed.add_field(name="الماب الحالي 🎮", value=f"**{map_name}**", inline=False)
                            embed.add_field(name="رابط الانضمام", value=f"[اضغط هنا للدخول](https://www.roblox.com/games/{curr_place})", inline=False)
                        elif curr_pres == 0:
                            embed.add_field(name="الحالة", value="أوفلاين 🔴", inline=False)
                        elif curr_pres == 1:
                            embed.add_field(name="الحالة", value="أونلاين في القائمة الرئيسية 🟢", inline=False)

                        await channel.send(embed=embed)
                        database.update_user_data(u_id, presence=curr_pres, place_id=curr_place)

                # 2. تتبع الأصدقاء بالأسماء
                f_data = await self.fetch_json(session, f"https://friends.roblox.com/v1/users/{u_id}/friends")
                if f_data and 'data' in f_data:
                    curr_friends_map = {f['id']: (f['name'], f['displayName']) for f in f_data['data']}
                    curr_ids = set(curr_friends_map.keys())
                    saved_ids = set(json.loads(friends_json)) if friends_json else set()

                    if saved_ids:
                        added_ids = curr_ids - saved_ids
                        for a_id in added_ids:
                            name, display = curr_friends_map.get(a_id, (f"ID: {a_id}", ""))
                            await channel.send(f"➕ **صديق جديد:** قام بإضافة `{display}` (@{name})")

                        removed_ids = saved_ids - curr_ids
                        for r_id in removed_ids:
                            r_name, r_display = await self.get_user_details(session, r_id)
                            await channel.send(f"➖ **حذف صديق:** قام بحذف `{r_display}` (@{r_name})")

                    database.update_user_data(u_id, friends_json=json.dumps(list(curr_ids)))

                # 3. تتبع البادجات
                b_data = await self.fetch_json(session, f"https://badges.roblox.com/v1/users/{u_id}/badges?sortOrder=Desc&limit=10")
                if b_data and 'data' in b_data:
                    curr_badge_ids = {b['id'] for b in b_data['data']}
                    saved_badges = set(map(int, k_badges.split(','))) if k_badges else set()
                    new_badges = curr_badge_ids - saved_badges

                    if new_badges and saved_badges:
                        for b_info in b_data['data']:
                            if b_info['id'] in new_badges:
                                embed = discord.Embed(title="🏅 الحصول على بادج جديد", color=discord.Color.gold())
                                embed.add_field(name="اسم البادج", value=b_info.get('name', 'غير معروف'))
                                embed.add_field(name="الوصف", value=b_info.get('description', 'لا يوجد'))
                                await channel.send(embed=embed)

                    database.update_user_data(u_id, badges_str=','.join(map(str, curr_badge_ids)))

    @tracker_loop.before_loop
    async def before_tracker(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def track(self, ctx, user_id: int):
        database.add_tracked_user(user_id, ctx.channel.id)
        await ctx.send(f"👁️ **بدأت المراقبة الكاملة بالأسماء للحساب:** `{user_id}`")

    @commands.command()
    async def untrack(self, ctx, user_id: int):
        database.remove_tracked_user(user_id)
        await ctx.send(f"🛑 **تم إيقاف المراقبة عن الحساب:** `{user_id}`")

async def setup(bot):
    await bot.add_cog(TrackerCog(bot))
