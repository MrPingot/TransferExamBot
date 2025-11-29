import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import random
import datetime
import traceback
from settings import *
from utils import *

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 核心：發送每日題目的功能 (給 main.py 和 rpg.py 呼叫) ---
    async def post_daily_task(self, subject_code, channel_id):
        if not channel_id: return "未設定頻道 ID"

        channel = self.bot.get_channel(channel_id)
        if not channel: return f"找不到頻道 {channel_id}"

        # 1. 讀取題庫
        base_path = os.path.join(QUESTION_DIR, subject_code)
        if not os.path.exists(base_path): return "題庫資料夾不存在"
        
        files = [f for f in os.listdir(base_path) if f.endswith('.json')]
        if not files: return "題庫是空的"

        try:
            # 2. 隨機選卷
            random_file = random.choice(files)
            with open(os.path.join(base_path, random_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data: return "檔案內容為空"
            
            # 3. 隨機選年份
            year = random.choice(list(data.keys()))
            content = data[year] # 這可能是字串或 list

            # 4. 解析資訊
            parts = random_file.split('_') # tua_a2_questions.json
            school_code = parts[0]
            group = parts[1].upper()
            subject_name = "微積分" if subject_code == "cal" else "普通物理"
            school_name = "台聯大" if school_code == "tua" else "台綜大"
            date_str = datetime.datetime.now().strftime("%m/%d")

            # 5. 指定題號
            target_q_str = ""
            if subject_code == "cal":
                if school_code == "tca": q_num = random.randint(1, 10) # 台綜 1~10
                elif school_code == "tua": q_num = random.randint(1, 8) # 台聯 1~8
                else: q_num = 1
                target_q_str = f"第 {q_num} 題"
            else:
                target_q_str = f"第 {random.randint(1, 20)} 題"

            # 6. 建立 View
            # is_daily=True -> 顯示領獎按鈕
            title = f"📅 {date_str} 每日挑戰：{school_name} {group}組 {subject_name}"
            view = UniversalPaperView(self.bot, title, content, user_id=None, is_daily=True)
            
            # 7. 發送 Embed
            embed = view.get_embed()
            embed.description = f"年份：{year} 年\n🎯 **今日指定題目：{target_q_str}**"
            
            message = await channel.send(embed=embed, view=view)

            # 8. 開啟討論串
            thread_name = f"📝 {date_str} {subject_name} {target_q_str} 解題區 ({school_name} {year})"
            await message.create_thread(name=thread_name, auto_archive_duration=1440)
            
            return f"✅ 成功發送：{thread_name}"

        except Exception as e:
            traceback.print_exc()
            return f"❌ 發生錯誤: {e}"

    # --- 查詢指令 ---
    @app_commands.command(name="題目", description="查詢歷屆考卷")
    @app_commands.describe(subject="科目", paper_code="考卷組別", year="年份")
    @app_commands.choices(
        subject=[app_commands.Choice(name="微積分", value="cal"), app_commands.Choice(name="普通物理", value="phy")],
        paper_code=[
            app_commands.Choice(name="台聯大 A2", value="tua_a2"), app_commands.Choice(name="台聯大 A3", value="tua_a3"),
            app_commands.Choice(name="台綜大 A", value="tca_a"), app_commands.Choice(name="台綜大 B", value="tca_b"),
            app_commands.Choice(name="台綜大 C", value="tca_c")
        ],
        year=[app_commands.Choice(name=f"{y}年", value=y) for y in range(103, 115) if y != 110]
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def search_question(self, interaction: discord.Interaction, subject: str, paper_code: str, year: int):
        school, group = paper_code.split('_')
        if school == "tca" and year < 105:
            return await interaction.response.send_message("❌ 台綜大題目只從 105 年開始。", ephemeral=True)

        filename = f"{school}_{group}_questions.json"
        file_path = os.path.join(QUESTION_DIR, subject, filename)
        
        if not os.path.exists(file_path):
            return await interaction.response.send_message(f"❌ 找不到題庫：{filename}", ephemeral=True)

        try:
            with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
            
            paper_data = data.get(str(year))
            if not paper_data:
                return await interaction.response.send_message(f"⚠️ 暫無 {year} 年資料。", ephemeral=True)

            school_name = "台聯大" if school == "tua" else "台綜大"
            title = f"📄 {school_name} {group.upper()}組 - {'微積分' if subject=='cal' else '普通物理'} {year}年"
            
            # is_daily=False -> 不顯示領獎按鈕，只有翻頁
            view = UniversalPaperView(self.bot, title, paper_data, user_id=interaction.user.id, is_daily=False)
            await interaction.response.send_message(embed=view.get_embed(), view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"錯誤：{e}", ephemeral=True)

    # --- 倒數與管理指令 ---
    @app_commands.command(name="查詢倒數", description="查看轉學考倒數")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def check_simple(self, interaction: discord.Interaction):
        now = datetime.datetime.now(TAIPEI_TZ)
        lines = [
            f"<:aya:1442919241262301204> Ciallo～(∠・ω< )⌒☆ ​今天是 {now.strftime('%Y年%m月%d日')} <:cute:1371194946035384411>",
            "--------------------------------",
            *[f"距離 **{e['name']}** 還剩 **{get_days_remaining(e['month'], e['day'])}** 天" for e in EXAMS]
        ]
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="開始倒數", description="啟用每日通知")
    @app_commands.default_permissions(administrator=True)
    async def start_notice(self, interaction: discord.Interaction, mention: bool, role: discord.Role = None):
        gid = str(interaction.guild_id)
        if gid in notification_channels: return await interaction.response.send_message("⚠️ 已啟用過！", ephemeral=True)
        notification_channels[gid] = NotificationConfig(interaction.channel.id, role.id if role else None)
        save_channels(notification_channels)
        await interaction.response.send_message("✅ 已啟用！")

    @app_commands.command(name="停止倒數", description="停用每日通知")
    @app_commands.default_permissions(administrator=True)
    async def stop_notice(self, interaction: discord.Interaction):
        gid = str(interaction.guild_id)
        if gid in notification_channels:
            del notification_channels[gid]
            save_channels(notification_channels)
            await interaction.response.send_message("❌ 已停用！")
        else: await interaction.response.send_message("⚠️ 尚未啟用！", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Study(bot))