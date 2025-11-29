import discord
from discord.ext import commands, tasks
import json
import os
import datetime
import settings
from utils import get_days_remaining, EXAMS 

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DATA_FILE = os.path.join(settings.BASE_DIR, 'users.json')
        self.STATE_FILE = os.path.join(settings.BASE_DIR, 'dashboard_state.json')
        self.message_id = self.load_state()
        self.update_task.start()

    def load_data(self):
        try:
            with open(self.DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def load_state(self):
        try:
            with open(self.STATE_FILE, 'r', encoding='utf-8') as f: return json.load(f).get("message_id")
        except: return None

    def save_state(self, msg_id):
        with open(self.STATE_FILE, 'w', encoding='utf-8') as f: json.dump({"message_id": msg_id}, f)

    def cog_unload(self):
        self.update_task.cancel()

    @tasks.loop(minutes=30)
    async def update_task(self):
        await self.bot.wait_until_ready()
        
        channel_id = settings.DASHBOARD_CHANNEL_ID
        if not channel_id: return
        channel = self.bot.get_channel(channel_id)
        if not channel: return

        users = self.load_data()
        if not users: return

        # 排序：等級 > 經驗
        sorted_users = sorted(users.items(), key=lambda x: (x[1]['level'], x[1]['exp']), reverse=True)

        now_str = datetime.datetime.now(settings.TAIPEI_TZ).strftime("%m/%d %H:%M")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 🔥 修改處：指定顯示台聯大倒數 (與 RPG 狀態同步)
        target_exam = next((e for e in EXAMS if '台聯' in e['name']), None)
        if target_exam:
            days = get_days_remaining(target_exam['month'], target_exam['day'])
            footer_text = f"距離 {target_exam['name']} 還有 {days} 天，大家加油！"
        else:
            min_days = min([get_days_remaining(e['month'], e['day']) for e in EXAMS])
            footer_text = f"距離考試還有 {min_days} 天，大家加油！"

        embed = discord.Embed(
            title="📊 轉學考戰情室",
            description=f"最後更新：{now_str} (每 30 分鐘刷新)",
            color=0x2ecc71
        )
        embed.set_footer(text=footer_text)

        for uid, u in sorted_users:
            # 檢查今日狀態
            is_quest_done = u.get("today_question_done", False) and u.get("last_action_date") == today
            is_signed = u.get("last_sign") == today
            study_hr = u.get("today_study_hours", 0) if u.get("last_action_date") == today else 0
            
            s = u['stats']
            
            value_text = (
                f"**Lv.{u['level']}** | {u['job']}\n"
                f"`💪{s['str']} 🧠{s['int']} 🍀{s['luk']} ❤️{s['vit']}`\n"
                f"📅簽到: {'✅' if is_signed else '⬛'} | ⏱️讀書: **{study_hr}**hr | 📝每日題: {'✅' if is_quest_done else '⬛'}"
            )
            
            embed.add_field(name=f"👤 {u['name']}", value=value_text, inline=False)

        try:
            if self.message_id:
                try:
                    msg = await channel.fetch_message(self.message_id)
                    await msg.edit(embed=embed)
                    return
                except discord.NotFound: pass 

            msg = await channel.send(embed=embed)
            self.message_id = msg.id
            self.save_state(msg.id)
        except Exception as e: print(f"Dashboard Error: {e}")

async def setup(bot):
    await bot.add_cog(Dashboard(bot))
