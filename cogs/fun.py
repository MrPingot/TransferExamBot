import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import json
import os
import math
import aiohttp
from settings import *

# ==========================================
# ⚔️ 技能資料庫 (設定招式、倍率、依賴屬性)
# ==========================================
# factor: 傷害依賴屬性 (str, int, luk)
# mult: 傷害倍率 (攻擊力 * mult)
# req_lv: 解鎖等級
SKILL_DB = {
    # --- 📐 微積分大師 (智力流) ---
    "微積分大師": [
        {"name": "極限運算", "req_lv": 1, "factor": "int", "mult": 1.2, "desc": "快速計算出了極限值！"},
        {"name": "微分打擊", "req_lv": 1, "factor": "int", "mult": 1.3, "desc": "對敵人的防禦進行微分，使其歸零！"},
        {"name": "羅必達法則", "req_lv": 5, "factor": "int", "mult": 1.8, "desc": "上下同時微分，造成巨大傷害！"},
        {"name": "積分轟炸", "req_lv": 10, "factor": "int", "mult": 2.2, "desc": "累積了無限的能量，進行定積分打擊！"},
        {"name": "泰勒展開式", "req_lv": 20, "factor": "int", "mult": 3.0, "desc": "展開了無窮級數，造成毀滅性打擊！"}
    ],
    # --- 🍎 物理大師 (力量流) ---
    "物理大師": [
        {"name": "自由落體", "req_lv": 1, "factor": "str", "mult": 1.2, "desc": "從高處丟下鐵球！"},
        {"name": "F=ma 重拳", "req_lv": 1, "factor": "str", "mult": 1.3, "desc": "施加了巨大的力，產生驚人加速度！"},
        {"name": "動量守恆衝撞", "req_lv": 5, "factor": "str", "mult": 1.8, "desc": "將全身動量灌注在這一擊！"},
        {"name": "電磁砲", "req_lv": 10, "factor": "str", "mult": 2.2, "desc": "利用洛倫茲力發射硬幣！"},
        {"name": "萬有引力墜落", "req_lv": 20, "factor": "str", "mult": 3.0, "desc": "召喚隕石，模擬行星撞擊！"}
    ],
    # --- 📖 英文大師 (運氣/爆擊流) ---
    "英文大師": [
        {"name": "單字連發", "req_lv": 1, "factor": "luk", "mult": 1.2, "desc": "快速背誦 7000 單字造成精神傷害！"},
        {"name": "文法修正", "req_lv": 1, "factor": "luk", "mult": 1.3, "desc": "指出了對手的語病，造成爆擊！"},
        {"name": "克漏字填空", "req_lv": 5, "factor": "luk", "mult": 1.8, "desc": "精準猜中了答案！"},
        {"name": "閱讀測驗", "req_lv": 10, "factor": "luk", "mult": 2.2, "desc": "用長篇大論讓對手頭昏眼花！"},
        {"name": "作文滿分", "req_lv": 20, "factor": "luk", "mult": 3.0, "desc": "寫出了優美的文章，感動了上蒼！"}
    ],
    # --- 💻 計概大師 (均衡流) ---
    "計概大師": [
        {"name": "Hello World", "req_lv": 1, "factor": "int", "mult": 1.2, "desc": "輸出了標準攻擊！"},
        {"name": "二進位打擊", "req_lv": 1, "factor": "str", "mult": 1.3, "desc": "用 0 和 1 瘋狂攻擊！"},
        {"name": "遞迴呼叫", "req_lv": 5, "factor": "int", "mult": 1.8, "desc": "一層又一層的攻擊，讓對手 Stack Overflow！"},
        {"name": "DDOS 攻擊", "req_lv": 10, "factor": "luk", "mult": 2.2, "desc": "發送大量封包癱瘓對手！"},
        {"name": "藍屏死機", "req_lv": 20, "factor": "str", "mult": 3.0, "desc": "強制對手重新開機！"}
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

    def get_user_data(self, user_id):
        """讀取最新玩家資料"""
        try:
            with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(str(user_id))
        except:
            return None

    def calculate_hp(self, level, vit):
        """計算血量: 基礎500 + 等級*50 + 體力*20"""
        return 500 + (level * 50) + (vit * 20)

    def calculate_damage(self, skill, stats):
        """計算傷害 (含屬性加成與浮動)"""
        # 1. 基礎傷害
        factor = skill['factor']
        base_dmg = stats.get(factor, 5) * 3  # 屬性 * 3 作為基傷
        
        # 2. 技能倍率
        final_dmg = base_dmg * skill['mult']
        
        # 3. 隨機浮動 (0.8 ~ 1.2)
        variance = random.uniform(0.8, 1.2)
        final_dmg *= variance
        
        # 4. 爆擊判定 (看 LUK)
        # 爆擊率 = LUK * 0.5% (最高 50%)
        crit_rate = min(stats['luk'] * 0.5, 50)
        is_crit = random.uniform(0, 100) < crit_rate
        
        if is_crit:
            final_dmg *= 1.5
            
        return int(final_dmg), is_crit

    # --- 抽老婆 (保留功能) ---
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

        # 1. 讀取雙方資料
        p1_data = self.get_user_data(interaction.user.id)
        p2_data = self.get_user_data(opponent.id)

        if not p1_data: return await interaction.response.send_message("❌ 你還沒註冊！請輸入 `/rpg註冊`", ephemeral=True)
        if not p2_data: return await interaction.response.send_message(f"❌ **{opponent.display_name}** 還沒註冊，不能決鬥！", ephemeral=True)

        # 2. 初始化戰鬥數值
        p1_name = p1_data['name']
        p2_name = p2_data['name']
        p1_job = p1_data['job']
        p2_job = p2_data['job']
        
        p1_hp = self.calculate_hp(p1_data['level'], p1_data['stats']['vit'])
        p2_hp = self.calculate_hp(p2_data['level'], p2_data['stats']['vit'])
        p1_max_hp = p1_hp
        p2_max_hp = p2_hp

        # 取得可用技能 (根據職業和等級)
        p1_skills = [s for s in SKILL_DB.get(p1_job, SKILL_DB["🥚 初心考生"]) if s['req_lv'] <= p1_data['level']]
        p2_skills = [s for s in SKILL_DB.get(p2_job, SKILL_DB["🥚 初心考生"]) if s['req_lv'] <= p2_data['level']]

        # 3. 開始戰鬥
        await interaction.response.send_message(
            f"⚔️ **決鬥開始！**\n"
            f"🔴 **{p1_name}** ({p1_job} Lv.{p1_data['level']}) HP: {p1_hp}\n"
            f"VS\n"
            f"🔵 **{p2_name}** ({p2_job} Lv.{p2_data['level']}) HP: {p2_hp}"
        )
        msg = await interaction.original_response()
        
        log = []
        turn = 1
        
        while p1_hp > 0 and p2_hp > 0:
            await asyncio.sleep(2) # 節奏控制
            
            # 隨機決定誰先手 (或是輪流) - 這裡用 50/50 增加刺激感
            is_p1_turn = random.choice([True, False])
            
            attacker_name = p1_name if is_p1_turn else p2_name
            attacker_data = p1_data if is_p1_turn else p2_data
            attacker_skills = p1_skills if is_p1_turn else p2_skills
            
            # 選擇技能 (等級高的技能機率稍微低一點，或者完全隨機)
            skill = random.choice(attacker_skills)
            
            # 計算傷害
            dmg, is_crit = self.calculate_damage(skill, attacker_data['stats'])
            
            # 扣血
            if is_p1_turn:
                p2_hp -= dmg
                victim_name = p2_name
            else:
                p1_hp -= dmg
                victim_name = p1_name
                
            # 產生戰鬥文字
            crit_text = " **(暴擊!)**" if is_crit else ""
            line = f"{'🔴' if is_p1_turn else '🔵'} **{attacker_name}** 使用了 **【{skill['name']}】**！\n   ↳ {skill['desc']} 造成 **{dmg}** 點傷害{crit_text}"
            log.append(line)
            
            # 只顯示最後 5 行
            display_log = "\n\n".join(log[-5:])
            
            # 製作 Embed 更新狀態
            embed = discord.Embed(title=f"⚔️ 回合 {turn} 激戰中...", description=display_log, color=0xffa500)
            
            # 血條顯示
            p1_pct = int((p1_hp / p1_max_hp) * 10)
            p2_pct = int((p2_hp / p2_max_hp) * 10)
            p1_bar = "🟩"*max(0, p1_pct) + "⬛"*max(0, 10-p1_pct)
            p2_bar = "🟩"*max(0, p2_pct) + "⬛"*max(0, 10-p2_pct)
            
            embed.add_field(name=f"{p1_name}", value=f"{p1_bar} ({max(0,p1_hp)}/{p1_max_hp})", inline=False)
            embed.add_field(name=f"{p2_name}", value=f"{p2_bar} ({max(0,p2_hp)}/{p2_max_hp})", inline=False)
            
            await msg.edit(content=None, embed=embed)
            turn += 1

        # 4. 結算
        winner = p1_name if p1_hp > 0 else p2_name
        winner_id = interaction.user.id if p1_hp > 0 else opponent.id
        loser_name = p2_name if p1_hp > 0 else p1_name
        
        # 發放獎勵
        rpg = self.bot.get_cog("RPG")
        bonus_text = ""
        if rpg:
            # 贏家 +30 EXP
            is_lv, new_lv = rpg.add_exp(winner_id, 30)
            bonus_text = f"\n🏆 獲得 **30 EXP**！"
            if is_lv: bonus_text += f"\n🎉 **升級了！Lv.{new_lv}**"

        embed_end = discord.Embed(title="🏆 決鬥結束！", color=0xffd700)
        embed_end.description = f"**{winner}** 擊敗了 **{loser_name}**！{bonus_text}"
        
        await msg.edit(embed=embed_end)

async def setup(bot):
    await bot.add_cog(Fun(bot))