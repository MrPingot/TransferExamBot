import discord
from discord.ext import commands
import asyncio
import datetime
import sys
import os
import traceback
import random
import json
from settings import *
from utils import *

# ==========================================
# 1. 初始化
# ==========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

# ==========================================
# 2. 每日挑戰專用 View (按鈕)
# ==========================================
class AutoDailyView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="解題完成！(+150 EXP)", style=discord.ButtonStyle.primary, emoji="🎯", custom_id="daily_btn_auto")
    async def complete_daily(self, interaction: discord.Interaction, button: discord.ui.Button):
        rpg = self.bot.get_cog("RPG")
        if not rpg: return await interaction.response.send_message("❌ RPG 未啟動", ephemeral=True)
        
        uid = str(interaction.user.id)
        rpg.check_daily_reset(uid)
        user_data = rpg.users.get(uid)
        
        if not user_data:
            return await interaction.response.send_message("請先 `/rpg註冊`。", ephemeral=True)
            
        if user_data.get("today_question_done"):
            return await interaction.response.send_message("⚠️ 你今天已經完成過每日挑戰囉！", ephemeral=True)
            
        is_lv, res = rpg.add_exp(uid, 150)
        user_data["today_question_done"] = True
        rpg.save_data()
        
        # 回覆玩家 (私密)
        msg = "🎯 **每日挑戰完成！** 獲得 **150** EXP！"
        if is_lv: msg += f"\n🎉 **升級了！Lv.{res}**"
        await interaction.response.send_message(msg, ephemeral=True)

        # 🔥 發送紀錄到 Log 頻道
        if LOG_CHANNEL_ID:
            log_ch = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_ch:
                embed = discord.Embed(description=f"🎯 完成了每日挑戰 (+150 EXP)", color=0xffd700, timestamp=datetime.datetime.now())
                embed.set_author(name=f"{interaction.user.display_name} (Lv.{user_data['level']})", icon_url=interaction.user.display_avatar.url)
                await log_ch.send(embed=embed)

# ==========================================
# 3. 核心功能函式
# ==========================================
async def load_extensions():
    extensions = ["cogs.study", "cogs.fun", "cogs.rpg", "cogs.dashboard"]
    
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ 載入成功: {ext}")
        except Exception:
            print(f"❌ 載入失敗: {ext}")
            traceback.print_exc()
async def update_vc_names():
    try:
        ust_days = next((get_days_remaining(e['month'], e['day']) for e in EXAMS if '台聯' in e['name']), 0)
        tcus_days = next((get_days_remaining(e['month'], e['day']) for e in EXAMS if '台綜' in e['name']), 0)
        if UST_VC_ID:
            ch = bot.get_channel(UST_VC_ID)
            if ch and ch.name != f"台聯大倒數--{ust_days}天": await ch.edit(name=f"台聯大倒數--{ust_days}天")
        if TCUS_VC_ID:
            ch = bot.get_channel(TCUS_VC_ID)
            if ch and ch.name != f"台綜大倒數--{tcus_days}天": await ch.edit(name=f"台綜大倒數--{tcus_days}天")
    except: pass

async def post_daily_question(subject_code, channel_id):
    if not channel_id: return
    channel = bot.get_channel(channel_id)
    if not channel: return

    base_path = os.path.join(QUESTION_DIR, subject_code)
    if not os.path.exists(base_path): return
    files = [f for f in os.listdir(base_path) if f.endswith('.json')]
    if not files: return

    try:
        random_file = random.choice(files)
        with open(os.path.join(base_path, random_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data: return
        year = random.choice(list(data.keys()))
        content = data[year]
        image_url = content[0] if isinstance(content, list) else content

        parts = random_file.split('_')
        school_code = parts[0]
        group = parts[1].upper()
        subject_name = "微積分" if subject_code == "cal" else "普通物理"
        date_str = datetime.datetime.now().strftime("%m/%d")

        target_q_str = ""
        if subject_code == "cal":
            if school_code == "tca": q_num = random.randint(1, 10)
            elif school_code == "tua": q_num = random.randint(1, 8)
            else: q_num = 1
            target_q_str = f"第 {q_num} 題"
        else:
            q_num = random.randint(1, 20)
            target_q_str = f"第 {q_num} 題"

        embed = discord.Embed(
            title=f"📅 {date_str} 每日挑戰：{school_code.upper()} {group}組 {subject_name}",
            description=f"年份：{year} 年\n🎯 **今日指定題目：{target_q_str}**\n\n⬇️ **請在下方討論串回答/討論** ⬇️",
            color=0xe74c3c
        )
        embed.set_image(url=image_url)
        
        view = AutoDailyView(bot)
        message = await channel.send(embed=embed, view=view)

        thread_name = f"📝 {date_str} {subject_name} {target_q_str} 解題區 ({school_code.upper()} {year})"
        await message.create_thread(name=thread_name, auto_archive_duration=1440)
        
        print(f"✅ 已發送每日挑戰 ({subject_name})")

    except Exception as e:
        print(f"❌ 發送失敗: {e}")
        traceback.print_exc()

# ==========================================
# 4. 定時任務迴圈
# ==========================================
async def daily_check():
    await bot.wait_until_ready()
    last_sent, last_vc, last_daily_q = None, None, None
    print("⏰ 定時任務監聽中...")
    
    while not bot.is_closed():
        try:
            now = datetime.datetime.now(TAIPEI_TZ)
            today = now.date()
            
            if now.hour == 0 and now.minute == 0 and last_vc != today:
                await update_vc_names()
                last_vc = today
                
            if now.hour == 8 and now.minute == 0 and last_sent != today:
                for gid, cfg in list(notification_channels.items()):
                    ch = bot.get_channel(cfg.channel_id)
                    if ch: asyncio.create_task(ch.send(create_notification_message(cfg)))
                save_channels(notification_channels)
                last_sent = today

            if now.hour == 8 and now.minute == 0 and last_daily_q != today:
                print("📝 開始發送每日題目...")
                await post_daily_question("cal", DAILY_CAL_CHANNEL_ID)
                await post_daily_question("phy", DAILY_PHY_CHANNEL_ID)
                last_daily_q = today

            await asyncio.sleep(30)
        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(30)

@bot.event
async def on_ready():
    print(f'🔥 {bot.user} 已上線')
    await bot.change_presence(activity=discord.Game(name="Ciallo～(∠・ω< )⌒☆", type=discord.ActivityType.playing))
    try:
        await bot.tree.sync()
        print("✅ 斜線指令同步完成")
    except Exception as e: print(f"❌ 同步錯誤: {e}")
    
    await update_vc_names()
    bot.loop.create_task(daily_check())

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # 🕵️ 私訊監控 (保留)
    if message.guild is None and DM_LOG_CHANNEL_ID:
        try:
            log_ch = bot.get_channel(DM_LOG_CHANNEL_ID)
            if log_ch:
                embed = discord.Embed(title="🕵️ 收到私訊", description=message.content, color=0x95a5a6)
                embed.set_author(name=f"{message.author}", icon_url=message.author.display_avatar.url)
                await log_ch.send(embed=embed)
        except: pass

    if message.channel.id == 1368547901189525574: await message.channel.send("----")
    await bot.process_commands(message)

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    if not TOKEN or TOKEN == '你的_NEW_TOKEN_HERE':
        print("❌ 請先去 settings.py 填入你的 Token！")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt: pass