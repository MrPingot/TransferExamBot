import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import datetime
import settings
from utils import get_days_remaining, EXAMS

# ==========================================
# ⚡ 神之名單 (白名單)
# ==========================================
# 在這裡填入可以執行 !god! 指令的使用者 ID (整數)
GOD_USERS = [
    1189944042671312959,  # 你自己 (原作者)
    1104431853181620284, # 朋友 A (範例，請改成真的 ID)
    # 987654321098765432, # 朋友 B
]

class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DATA_FILE = os.path.join(settings.BASE_DIR, 'users.json')
        self.users = self.load_data()

    def load_data(self):
        try:
            with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_data(self):
        with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=4, ensure_ascii=False)

    def add_exp(self, user_id, amount):
        uid = str(user_id)
        if uid not in self.users: return False, "尚未註冊"
        user = self.users[uid]
        if user['level'] >= 99: return False, "MAX"
        
        user['exp'] += amount
        req_exp = user['level'] * 15
        leveled_up = False
        
        while user['exp'] >= req_exp:
            if user['level'] >= 99:
                user['exp'] = 0
                break
            user['exp'] -= req_exp
            user['level'] += 1
            leveled_up = True
            
            s = user['stats']; job = user['job']
            if job == "微積分大師":
                s['int'] += 4; s['vit'] += 1
            elif job == "物理大師":
                s['str'] += 4; s['vit'] += 1
            elif job == "英文大師":
                s['luk'] += 4; s['str'] += 1
            elif job == "計概大師":
                s['str'] += 2; s['int'] += 2; s['vit'] += 1
            else:
                s['str'] += 1; s['int'] += 1; s['vit'] += 1; s['luk'] += 1
            
            req_exp = user['level'] * 15
            
        self.save_data()
        return leveled_up, user['level']

    def check_daily_reset(self, uid):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        user = self.users[uid]
        if user.get("last_action_date") != today:
            user["last_action_date"] = today
            user["today_study_hours"] = 0
            user["today_question_done"] = False
            self.save_data()

    # --- 內部工具：發送紀錄 ---
    async def send_log(self, interaction, content):
        if settings.LOG_CHANNEL_ID:
            channel = self.bot.get_channel(settings.LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(description=content, color=0x00ff00, timestamp=datetime.datetime.now())
                try:
                    embed.set_author(name=f"{interaction.user.display_name} (Lv.{self.users[str(interaction.user.id)]['level']})", icon_url=interaction.user.display_avatar.url)
                except:
                    embed.set_author(name=f"{interaction.user.display_name}")
                await channel.send(embed=embed)

    # --- 指令區 ---
    @app_commands.command(name="rpg註冊", description="建立檔案")
    async def register(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        if uid in self.users: return await interaction.response.send_message("已註冊！", ephemeral=False)
        self.users[uid] = {
            "name": interaction.user.display_name,
            "job": "🥚 初心考生",
            "level": 1,
            "exp": 0,
            "stats": {"str": 5, "int": 5, "vit": 5, "luk": 5},
            "last_sign": "",
            "streak": 0,
            "last_action_date": "",
            "today_study_hours": 0,
            "today_question_done": False
        }
        self.save_data()
        await interaction.response.send_message(f"✅ 註冊成功！", ephemeral=False)
        await self.send_log(interaction, "🆕 註冊了考生檔案")

    @app_commands.command(name="rpg狀態", description="查看狀態")
    async def status(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        if uid not in self.users: return await interaction.response.send_message("請先 `/rpg註冊`。", ephemeral=True)
        self.check_daily_reset(uid)
        u = self.users[uid]; lvl = u['level']
        
        if lvl >= 99:
            req_exp = 999999
            exp_display = "👑 已達巔峰 👑"
        else:
            req_exp = lvl * 15
            bar_len = 10
            safe_exp = min(u['exp'], req_exp)
            filled = int((safe_exp / req_exp) * bar_len)
            exp_display = "🟦"*filled + "⬜"*(bar_len-filled)

        target_exam = next((e for e in EXAMS if '台聯' in e['name']), None)
        if target_exam:
            days = get_days_remaining(target_exam['month'], target_exam['day'])
            footer_text = f"距離 {target_exam['name']} 還有 {days} 天，加油！"
        else:
            footer_text = "距離考試還有 ??? 天"

        embed = discord.Embed(title=f"📜 {u['name']} 的檔案", color=0xf1c40f)
        embed.add_field(name="職業", value=u['job'], inline=True)
        embed.add_field(name="等級", value=f"Lv. {lvl}", inline=True)
        embed.add_field(name="經驗值", value=f"{u['exp']} / {req_exp}\n{exp_display}", inline=False)
        
        daily_txt = (
            f"📆 連續簽到: **{u.get('streak', 0)}** 天\n"
            f"⏱️ 今日讀書: **{u.get('today_study_hours', 0)} / 10** 小時\n"
            f"📝 每日一題: {'✅ 完成' if u.get('today_question_done') else '❌'}"
        )
        embed.add_field(name="📅 今日修練", value=daily_txt, inline=False)
        
        s = u['stats']
        stats_txt = f"💪STR: {s['str']} | 🧠INT: {s['int']} | 🍀LUK: {s['luk']} | ❤️VIT: {s['vit']}"
        embed.add_field(name="屬性", value=stats_txt, inline=False)
        embed.set_footer(text=footer_text)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="簽到", description="每日簽到")
    async def sign_in(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        if uid not in self.users: return await interaction.response.send_message("未註冊", ephemeral=True)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        u = self.users[uid]
        if u.get("last_sign") == today: return await interaction.response.send_message("⚠️ 今天已簽到過了！", ephemeral=True)
        if u.get("last_sign") == yesterday: u["streak"] += 1
        else: u["streak"] = 1
        exp = 50 + min(u["streak"], 10)*5
        u["last_sign"] = today
        is_lv, res = self.add_exp(uid, exp)
        msg = f"📅 **{interaction.user.display_name}** 簽到成功！獲得 {exp} EXP！"
        if is_lv: msg += f"\n🎉 **升級了！Lv.{res}**"
        await interaction.response.send_message(msg, ephemeral=False)
        await self.send_log(interaction, f"📅 完成簽到 (連續 {u['streak']} 天) (+{exp} EXP)")

    @app_commands.command(name="讀書", description="回報時數")
    async def study_report(self, interaction: discord.Interaction, hours: float):
        uid = str(interaction.user.id)
        if uid not in self.users: return await interaction.response.send_message("未註冊", ephemeral=True)
        self.check_daily_reset(uid)
        u = self.users[uid]
        if hours <= 0: return await interaction.response.send_message("時間錯誤", ephemeral=True)
        rem = 10 - u.get("today_study_hours", 0)
        if rem <= 0: return await interaction.response.send_message("今日已滿 10 小時", ephemeral=True)
        act = min(hours, rem)
        exp = int(act * 20)
        u["today_study_hours"] += act
        is_lv, res = self.add_exp(uid, exp)
        msg = f"⏱️ **{interaction.user.display_name}** 讀了 {act} 小時，獲得 {exp} EXP！"
        if is_lv: msg += f"\n🎉 **升級了！Lv.{res}**"
        await interaction.response.send_message(msg, ephemeral=False)
        await self.send_log(interaction, f"📚 回報讀書 **{act}** 小時 (+{exp} EXP)\n今日累計：{u['today_study_hours']} hr")

    @app_commands.command(name="rpg轉職", description="Lv.5 轉職")
    async def change_job(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        if uid not in self.users: 
            return await interaction.response.send_message("❌ 請先 `/rpg註冊`。", ephemeral=True)
        
        u = self.users[uid]
        if u['level'] < 5:
            return await interaction.response.send_message(f"⚠️ 等級不足！你需要 **Lv.5** 才能轉職 (目前 Lv.{u['level']})。", ephemeral=True)
        
        if u['job'] != "🥚 初心考生":
            return await interaction.response.send_message("你已經轉職過了！無法更換職業。", ephemeral=True)

        embed = discord.Embed(title="🏰 轉職大廳", description=f"恭喜 **{u['name']}** 達到 Lv.5！", color=0x00ff00)
        embed.add_field(name="📐 微積分大師 (Intellect)", value="• 定位: 玻璃大砲\n• 成長: `INT+4`, `VIT+1`", inline=False)
        embed.add_field(name="🍎 物理大師 (Strength)", value="• 定位: 重裝戰士\n• 成長: `STR+4`, `VIT+1`", inline=False)
        embed.add_field(name="💻 計概大師 (Balanced)", value="• 定位: 全能型\n• 成長: `STR+2`, `INT+2`, `VIT+1`", inline=False)
        embed.add_field(name="📖 英文大師 (Luck)", value="• 定位: 爆擊流\n• 成長: `LUK+4`, `STR+1`", inline=False)
        
        view = JobSelectView(self, uid)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # 😈 GM 指令 (多人權限版)
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        if message.content.startswith("!god!"):

            # 2. 🔥 驗證白名單 (只有名單內的人可以用)
            if message.author.id not in GOD_USERS: return

            try:      
                args = message.content.split()
                if len(args) < 3: return
                cmd_type, val = args[1].lower(), args[2]

                if cmd_type == "speak":
                    if len(args) < 4: return
                    target_ch_id = int(args[2])
                    content = " ".join(args[3:])
                    target_ch = self.bot.get_channel(target_ch_id)
                    if target_ch:
                        await target_ch.send(content)
                        await message.channel.send(f"✅ 已發送至 {target_ch.mention}", delete_after=5)
                    else:
                        await message.channel.send("❌ 找不到頻道", delete_after=5)
                    return

                if cmd_type == "post":
                    study_cog = self.bot.get_cog("Study")
                    cid = settings.DAILY_CAL_CHANNEL_ID if val == "cal" else settings.DAILY_PHY_CHANNEL_ID
                    if study_cog:
                        res = await study_cog.post_daily_task(val, cid)
                        await message.channel.send(f"🚀 {res}", delete_after=5)
                    return

                tid = str(message.mentions[0].id) if message.mentions else str(message.author.id)
                tname = message.mentions[0].display_name if message.mentions else message.author.display_name
                if tid not in self.users: return
                u = self.users[tid]
                
                if cmd_type in ['str', 'int', 'vit', 'luk']: u['stats'][cmd_type] = int(val)
                elif cmd_type in ['level', 'exp']: u[cmd_type] = int(val)
                elif cmd_type == 'job': u['job'] = val
                
                self.save_data()
                await message.channel.send(f"⚡ {tname} {cmd_type} -> {val}", delete_after=5)
            except Exception as e:
                await message.channel.send(f"❌ {e}", delete_after=5)

class JobSelectView(discord.ui.View):
    def __init__(self, rpg, uid): super().__init__(timeout=60); self.rpg=rpg; self.uid=uid
    async def p(self, i, j):
        if str(i.user.id)!=self.uid: return
        self.rpg.users[self.uid]['job']=j; s=self.rpg.users[self.uid]['stats']
        if "微積分" in j: s['int']+=10
        elif "物理" in j: s['str']+=10
        elif "英文" in j: s['luk']+=10
        elif "計概" in j: s['str']+=3;s['int']+=3;s['luk']+=3
        self.rpg.save_data(); await i.response.edit_message(content=f"🎉 轉職成功！你現在是 **{j}** 了！", embed=None, view=None)
        await self.rpg.send_log(i, f"🔄 轉職成為 **{j}**")
    @discord.ui.button(label="微積分", emoji="📐") 
    async def b1(self, i, b): await self.p(i, "微積分大師")
    @discord.ui.button(label="物理", emoji="🍎") 
    async def b2(self, i, b): await self.p(i, "物理大師")
    @discord.ui.button(label="計概", emoji="💻") 
    async def b3(self, i, b): await self.p(i, "計概大師")
    @discord.ui.button(label="英文", emoji="📖") 
    async def b4(self, i, b): await self.p(i, "英文大師")

async def setup(bot): await bot.add_cog(RPG(bot))
