import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import json
import os
import aiohttp
import datetime # ✅ 新增這個
from settings import *

# ==========================================
# ⚔️ 技能資料庫 (擴充版)
# ==========================================
SKILL_DB = {
    # --- 📐 微積分大師 ---
    "微積分大師": [
        {"name": "極限運算", "req_lv": 1, "factor": "int", "mult": 1.2, "desc": "快速計算出了極限值！"},
        {"name": "連續性檢查", "req_lv": 5, "factor": "int", "mult": 1.5, "desc": "確認了函式的連續性，發動攻擊！"},
        {"name": "羅必達法則", "req_lv": 10, "factor": "int", "mult": 1.8, "desc": "上下同時微分，造成巨大傷害！"},
        {"name": "隱函數微分", "req_lv": 15, "factor": "int", "mult": 2.2, "desc": "從沒想過的角度進行微分攻擊！"},
        {"name": "黎曼和轟炸", "req_lv": 20, "factor": "int", "mult": 2.6, "desc": "切分成無數個小矩形砸向對手！"},
        {"name": "泰勒展開式", "req_lv": 25, "factor": "int", "mult": 3.0, "desc": "展開了無窮級數，造成毀滅性打擊！"},
        {"name": "多重積分", "req_lv": 30, "factor": "int", "mult": 3.5, "desc": "三重積分的重量壓得對手喘不過氣！"},
        {"name": "格林公式", "req_lv": 35, "factor": "int", "mult": 4.0, "desc": "沿著封閉曲線進行環路攻擊！"},
        {"name": "傅立葉變換", "req_lv": 40, "factor": "int", "mult": 4.8, "desc": "將對手轉換到頻域並粉碎！"},
        {"name": "納維-斯托克斯", "req_lv": 50, "factor": "int", "mult": 6.0, "desc": "用千禧年難題的混沌亂流吞沒對手！"}
    ],
    # --- 🍎 物理大師 ---
    "物理大師": [
        {"name": "自由落體", "req_lv": 1, "factor": "str", "mult": 1.2, "desc": "從高處丟下鐵球！"},
        {"name": "摩擦力生熱", "req_lv": 5, "factor": "str", "mult": 1.5, "desc": "高速摩擦造成燒傷！"},
        {"name": "動量守恆衝撞", "req_lv": 10, "factor": "str", "mult": 1.8, "desc": "將全身動量灌注在這一擊！"},
        {"name": "簡諧運動", "req_lv": 15, "factor": "str", "mult": 2.2, "desc": "來回擺盪的重拳，讓人無法捉摸！"},
        {"name": "萬有引力墜落", "req_lv": 20, "factor": "str", "mult": 2.6, "desc": "召喚小行星撞擊對手！"},
        {"name": "電磁感應砲", "req_lv": 25, "factor": "str", "mult": 3.0, "desc": "利用磁通量變化產生強大電流！"},
        {"name": "熱力學第二定律", "req_lv": 30, "factor": "str", "mult": 3.5, "desc": "增加對手的亂度(Entropy)，使其崩潰！"},
        {"name": "量子穿隧", "req_lv": 35, "factor": "str", "mult": 4.0, "desc": "無視防禦，直接穿過護甲攻擊本體！"},
        {"name": "相對論重拳", "req_lv": 40, "factor": "str", "mult": 4.8, "desc": "接近光速的一拳，質量無限大！"},
        {"name": "黑洞視界", "req_lv": 50, "factor": "str", "mult": 6.0, "desc": "連光都無法逃脫的重力場！"}
    ],
    # --- 📖 英文大師 ---
    "英文大師": [
        {"name": "單字連發", "req_lv": 1, "factor": "luk", "mult": 1.2, "desc": "快速背誦 7000 單字造成精神傷害！"},
        {"name": "文法修正", "req_lv": 5, "factor": "luk", "mult": 1.5, "desc": "指出了對手的語病，造成爆擊！"},
        {"name": "克漏字填空", "req_lv": 10, "factor": "luk", "mult": 1.8, "desc": "精準猜中了答案！"},
        {"name": "倒裝句法", "req_lv": 15, "factor": "luk", "mult": 2.2, "desc": "Never have I seen such power!"},
        {"name": "作文滿分", "req_lv": 20, "factor": "luk", "mult": 2.6, "desc": "寫出了優美的文章，感動了上蒼！"},
        {"name": "GRE 紅寶書", "req_lv": 25, "factor": "luk", "mult": 3.0, "desc": "丟出厚重的單字書砸向對手！"},
        {"name": "莎士比亞十四行詩", "req_lv": 30, "factor": "luk", "mult": 3.5, "desc": "古典文學的靈魂衝擊！"},
        {"name": "經濟學人閱讀", "req_lv": 35, "factor": "luk", "mult": 4.0, "desc": "艱澀的長難句讓對手大腦當機！"},
        {"name": "Pneumono...", "req_lv": 40, "factor": "luk", "mult": 1.0, "is_ohko": True, "desc": "唸出了世上最長的單字，試圖讓對手窒息！(機率秒殺)"},
        {"name": "韋氏大字典", "req_lv": 50, "factor": "luk", "mult": 6.0, "desc": "召喚整本字典的知識量壓垮對手！"}
    ],
    # --- 💻 計概大師 ---
    "計概大師": [
        {"name": "Hello World", "req_lv": 1, "factor": "int", "mult": 1.2, "desc": "輸出了標準攻擊！"},
        {"name": "二進位打擊", "req_lv": 5, "factor": "str", "mult": 1.5, "desc": "用 0 和 1 瘋狂攻擊！"},
        {"name": "遞迴呼叫", "req_lv": 10, "factor": "int", "mult": 1.8, "desc": "一層又一層的攻擊，讓對手 Stack Overflow！"},
        {"name": "指標錯誤", "req_lv": 15, "factor": "luk", "mult": 2.2, "desc": "Segmentation Fault (Core Dumped)！"},
        {"name": "DDOS 攻擊", "req_lv": 20, "factor": "int", "mult": 2.6, "desc": "發送大量封包癱瘓對手！"},
        {"name": "SQL Injection", "req_lv": 25, "factor": "int", "mult": 3.0, "desc": "' OR 1=1; DROP TABLE Opponent; --"},
        {"name": "藍屏死機", "req_lv": 30, "factor": "str", "mult": 3.5, "desc": "強制對手重新開機！"},
        {"name": "機器學習", "req_lv": 35, "factor": "int", "mult": 4.0, "desc": "AI 分析出了對手的弱點！"},
        {"name": "區塊鏈打擊", "req_lv": 40, "factor": "luk", "mult": 4.8, "desc": "去中心化的分散式攻擊！"},
        {"name": "sudo rm -rf /", "req_lv": 50, "factor": "str", "mult": 6.0, "desc": "獲取最高權限，刪除對手根目錄！"}
    ],
    # --- 🥚 初心考生 ---
    "🥚 初心考生": [
        {"name": "丟鉛筆", "req_lv": 1, "factor": "str", "mult": 1.1, "desc": "丟出了 2B 鉛筆！"},
        {"name": "猜 C", "req_lv": 1, "factor": "luk", "mult": 1.1, "desc": "不知道選什麼，猜 C 就對了！"},
        {"name": "熬夜", "req_lv": 5, "factor": "vit", "mult": 1.5, "desc": "用肝換取了攻擊力！"}
    ]
}

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DATA_FILE = os.path.join(BASE_DIR, 'users.json')

    # 改為直接從 RPG Cog 讀取記憶體中的資料，避免不同步
    def get_rpg_cog(self):
        return self.bot.get_cog("RPG")

    def calculate_hp(self, level, vit):
        return 150 + (level * 50) + (vit * 20)

    def calculate_damage(self, skill, stats):
        if skill.get("is_ohko"):
            chance = min(5 + (stats['luk'] * 0.2), 30)
            if random.uniform(0, 100) < chance: return 999999, True
            else: return 10, False

        factor = skill['factor']
        base_dmg = stats.get(factor, 5) * 3 
        raw_dmg = base_dmg * skill['mult']
        
        if skill['mult'] >= 2.5: variance = random.uniform(0.95, 1.3)
        else: variance = random.uniform(0.8, 1.2)
            
        final_dmg = raw_dmg * variance
        
        crit_rate = min(stats['luk'] * 0.5, 50)
        is_crit = random.uniform(0, 100) < crit_rate
        if is_crit: final_dmg *= 1.5
            
        return int(final_dmg), is_crit

    @app_commands.command(name="抽老婆", description="隨機召喚一張動漫老婆圖")
    async def waifu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get('https://api.waifu.pics/sfw/waifu') as r:
                    d = await r.json()
                    await interaction.followup.send(embed=discord.Embed(title="😍 你的老婆出現了！", color=0xff69b4).set_image(url=d['url']))
        except Exception as e: await interaction.followup.send(f"錯誤: {e}")

    # --- ⚔️ 職業決鬥系統 ---
    @app_commands.command(name="決鬥", description="使用你的職業與數值進行對戰！")
    async def duel(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.bot: return await interaction.response.send_message("不能跟機器人打！", ephemeral=True)
        if opponent == interaction.user: return await interaction.response.send_message("不能跟自己打！", ephemeral=True)

        # 1. 取得 RPG 系統資料
        rpg = self.get_rpg_cog()
        if not rpg: return await interaction.response.send_message("RPG 系統未啟動", ephemeral=True)

        p1_id = str(interaction.user.id)
        p2_id = str(opponent.id)

        p1_data = rpg.users.get(p1_id)
        p2_data = rpg.users.get(p2_id)

        if not p1_data: return await interaction.response.send_message("❌ 你還沒註冊！請輸入 `/rpg註冊`", ephemeral=True)
        if not p2_data: return await interaction.response.send_message(f"❌ **{opponent.display_name}** 還沒註冊！", ephemeral=True)

        # 2. 判斷是否為「每日首戰」
        # 我們檢查發起人 (p1) 今天有沒有打過
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        is_daily_match = False
        
        # 如果 last_duel_date 不存在或不是今天，就代表是首戰
        if p1_data.get("last_duel_date") != today:
            is_daily_match = True
            p1_data["last_duel_date"] = today # 寫入今天日期
            rpg.save_data() # 立即存檔，避免重複觸發

        # 標題
        title_text = "⚔️ **決鬥開始！**"
        if is_daily_match:
            title_text = "🔥 **決鬥開始！(每日積分賽)** 🔥\n*勝者將獲得 50 EXP！*"

        # 3. 初始化戰鬥
        p1_name, p2_name = p1_data['name'], p2_data['name']
        p1_job, p2_job = p1_data['job'], p2_data['job']
        
        p1_hp = self.calculate_hp(p1_data['level'], p1_data['stats']['vit'])
        p2_hp = self.calculate_hp(p2_data['level'], p2_data['stats']['vit'])
        p1_max, p2_max = p1_hp, p2_hp

        # 取得技能
        p1_skills = [s for s in SKILL_DB.get(p1_job, SKILL_DB["🥚 初心考生"]) if s['req_lv'] <= p1_data['level']]
        p2_skills = [s for s in SKILL_DB.get(p2_job, SKILL_DB["🥚 初心考生"]) if s['req_lv'] <= p2_data['level']]
        if not p1_skills: p1_skills = SKILL_DB["🥚 初心考生"]
        if not p2_skills: p2_skills = SKILL_DB["🥚 初心考生"]

        await interaction.response.send_message(
            f"{title_text}\n"
            f"🔴 **{p1_name}** (Lv.{p1_data['level']}) HP: {p1_hp}\n"
            f"VS\n"
            f"🔵 **{p2_name}** (Lv.{p2_data['level']}) HP: {p2_hp}"
        )
        msg = await interaction.original_response()
        
        log = []
        turn = 1
        
        # 戰鬥迴圈
        while p1_hp > 0 and p2_hp > 0:
            await asyncio.sleep(2)
            is_p1_turn = random.choice([True, False])
            
            atk_name = p1_name if is_p1_turn else p2_name
            atk_data = p1_data if is_p1_turn else p2_data
            atk_skills = p1_skills if is_p1_turn else p2_skills
            
            skill = random.choice(atk_skills)
            dmg, is_crit = self.calculate_damage(skill, atk_data['stats'])
            
            if is_p1_turn: p2_hp -= dmg
            else: p1_hp -= dmg
                
            crit_str = " **(⚡致命一擊!)**" if is_crit and dmg < 900000 else ""
            if dmg > 900000: crit_str = " **(💀 一擊必殺!)**"
            
            line = f"{'🔴' if is_p1_turn else '🔵'} **{atk_name}** 使用了 **【{skill['name']}】**！\n   ↳ {skill['desc']} 造成 **{dmg}** 點傷害{crit_str}"
            log.append(line)
            
            display_log = "\n\n".join(log[-5:])
            embed = discord.Embed(title=f"⚔️ 回合 {turn}", description=display_log, color=0xffa500)
            
            p1_pct = int((p1_hp / p1_max) * 10)
            p2_pct = int((p2_hp / p2_max) * 10)
            p1_bar = "🟩"*max(0, p1_pct) + "⬛"*max(0, 10-p1_pct)
            p2_bar = "🟩"*max(0, p2_pct) + "⬛"*max(0, 10-p2_pct)
            
            embed.add_field(name=f"{p1_name}", value=f"{p1_bar} ({max(0,p1_hp)}/{p1_max})", inline=False)
            embed.add_field(name=f"{p2_name}", value=f"{p2_bar} ({max(0,p2_hp)}/{p2_max})", inline=False)
            
            await msg.edit(content=None, embed=embed)
            turn += 1

        winner = p1_name if p1_hp > 0 else p2_name
        winner_id = interaction.user.id if p1_hp > 0 else opponent.id
        loser_name = p2_name if p1_hp > 0 else p1_name
        
        # 獎勵結算
        bonus_text = ""
        
        # 🔥 如果是每日積分賽，贏家獲得 50 EXP
        if is_daily_match:
            is_lv, new_lv = rpg.add_exp(winner_id, 50)
            bonus_text = f"\n🏆 **每日首戰勝利**！獲得 **50 EXP**！"
            if is_lv: bonus_text += f"\n🎉 **升級了！Lv.{new_lv}**"
        
        # 合併顯示最後戰報
        final_log = "\n\n".join(log[-5:])
        
        end_embed = discord.Embed(title="🏆 決鬥結束！", color=0xffd700)
        end_embed.description = f"{final_log}\n\n━━━━━━━━━━━━━━\n**{winner}** 擊敗了 **{loser_name}**！{bonus_text}"
        
        await msg.edit(embed=end_embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
