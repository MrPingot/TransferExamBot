import os
import pytz

# ==========================
# 🔐 敏感資料
# ==========================
TOKEN = ''  # ⚠️ 填入你的 Token

# ==========================
# ⚙️ 頻道 ID 設定
# ==========================
UST_VC_ID = 1443276863534534871     # 台聯大語音頻道
TCUS_VC_ID = 1443276929565327480    # 台綜大語音頻道

# 每日挑戰發送頻道 (0 代表關閉)
DAILY_CAL_CHANNEL_ID = 1442155400525906011  # 微積分
DAILY_PHY_CHANNEL_ID = 0                    # 物理
DASHBOARD_CHANNEL_ID = 1444374676695683234
DM_LOG_CHANNEL_ID = 999898465263947816
LOG_CHANNEL_ID = 999898465263947816
# ==========================
# 📅 日期與路徑
# ==========================
TAIPEI_TZ = pytz.timezone('Asia/Taipei')

EXAMS = [
    {'name': '北大轉學考', 'month': 6, 'day': 14},
    {'name': '台大/台聯大轉學考', 'month': 6, 'day': 27},
    {'name': '政大轉學考', 'month': 7, 'day': 2},
    {'name': '台綜大轉學考', 'month': 7, 'day': 22}
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNELS_FILE = os.path.join(BASE_DIR, 'channels.json')
QUOTES_FILE = os.path.join(BASE_DIR, 'good.json')
QUESTION_DIR = os.path.join(BASE_DIR, 'question')