import json
import datetime
import random
import os
import discord
from settings import *

# --- 資料結構 ---
class NotificationConfig:
    def __init__(self, channel_id, mention_role=None):
        self.channel_id = channel_id
        self.mention_role = mention_role
    def to_dict(self): return {'channel_id': self.channel_id, 'mention_role': self.mention_role}
    @classmethod
    def from_dict(cls, data): return cls(channel_id=data['channel_id'], mention_role=data.get('mention_role'))

# --- 讀寫 JSON ---
def load_channels():
    try:
        with open(CHANNELS_FILE, 'r') as f:
            data = json.load(f)
            return {gid: NotificationConfig.from_dict(cfg) for gid, cfg in data.items()}
    except: return {}

def save_channels(channels):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump({gid: cfg.to_dict() for gid, cfg in channels.items()}, f, indent=2)

def load_quotes():
    try:
        with open(QUOTES_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return [{"quote": "堅持到底。", "author": "佚名"}]

notification_channels = load_channels()
quotes = load_quotes()

# --- 計算邏輯 ---
def get_days_remaining(tm, td):
    now = datetime.datetime.now(TAIPEI_TZ)
    target = TAIPEI_TZ.localize(datetime.datetime(now.year, tm, td))
    if now > target: target = TAIPEI_TZ.localize(datetime.datetime(now.year + 1, tm, td))
    return (target - now).days

def create_notification_message(config):
    now = datetime.datetime.now(TAIPEI_TZ)
    q = random.choice(quotes)
    lines = [
        f"<:aya:1442919241262301204> 早安{' <@&'+str(config.mention_role)+'>' if config.mention_role else ''}！今天是 {now.strftime('%Y年%m月%d日')} <:cute:1371194946035384411>\n",
        *[f"距離 **{e['name']}** 還剩 **{get_days_remaining(e['month'], e['day'])}** 天" for e in EXAMS],
        f"\n{q['quote']}\n——{q['author']}"
    ]
    return "\n".join(lines)

# ==========================================
# 🆕 通用考卷視圖 (支援翻頁 + 每日挑戰獎勵)
# ==========================================
class UniversalPaperView(discord.ui.View):
    def __init__(self, bot, title, images, user_id=None, is_daily=False):
        # 每日挑戰永久有效，一般查詢10分鐘有效
        super().__init__(timeout=None if is_daily else 600)
        
        self.bot = bot
        self.title = title
        self.images = images if isinstance(images, list) else [images]
        self.current_page = 0
        self.user_id = user_id
        self.is_daily = is_daily 

        # 如果不是每日挑戰，就移除領獎按鈕
        if not self.is_daily:
            self.remove_item(self.claim_btn)

        # 如果只有一頁，移除翻頁按鈕
        if len(self.images) <= 1:
            self.remove_item(self.prev_btn)
            self.remove_item(self.page_counter)
            self.remove_item(self.next_btn)
        else:
            self.update_buttons()

    def update_buttons(self):
        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page == len(self.images) - 1)
        self.page_counter.label = f"第 {self.current_page + 1} / {len(self.images)} 頁"

    def get_embed(self):
        embed = discord.Embed(title=self.title, color=0xe74c3c if self.is_daily else 0x00bfff)
        embed.set_image(url=self.images[self.current_page])
        
        footer_text = "⬇️ 請在討論串回答" if self.is_daily else f"共 {len(self.images)} 頁"
        if len(self.images) > 1 and not self.is_daily: footer_text += " | 可翻頁"
        embed.set_footer(text=footer_text)
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # 一般查詢模式：只有查詢者能翻頁
        if not self.is_daily and self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你查的考卷喔！", ephemeral=True)
            return False
        return True

    # --- 翻頁按鈕 ---
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.primary, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="頁碼", style=discord.ButtonStyle.grey, disabled=True, row=0)
    async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button): pass

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.primary, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # --- 領取經驗按鈕 (只有每日挑戰會有) ---
    @discord.ui.button(label="解題完成！(+150 EXP)", style=discord.ButtonStyle.danger, emoji="🎯", custom_id="daily_claim_btn", row=1)
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        rpg = self.bot.get_cog("RPG")
        if not rpg: return await interaction.response.send_message("❌ RPG 未啟動", ephemeral=True)
        
        uid = str(interaction.user.id)
        
        # 每日挑戰邏輯
        rpg.check_daily_reset(uid)
        user_data = rpg.users.get(uid)
        if not user_data: return await interaction.response.send_message("請先 `/rpg註冊`。", ephemeral=True)
        if user_data.get("today_question_done"):
            return await interaction.response.send_message("⚠️ 你今天已經完成過每日挑戰囉！", ephemeral=True)
        
        is_lv, res = rpg.add_exp(uid, 150)
        user_data["today_question_done"] = True
        rpg.save_data()
        
        msg = "🎯 **每日挑戰完成！** 獲得 **150** EXP！"
        if is_lv: msg += f"\n🎉 **升級了！Lv.{res}**"
        
        await interaction.followup.send(msg, ephemeral=True)