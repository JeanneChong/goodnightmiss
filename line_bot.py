import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from bs4 import BeautifulSoup
import schedule
import threading
import sqlite3
from datetime import datetime, timedelta
import random

# 初始化 Flask 應用程式
app = Flask(__name__)

# 設定 Line Bot 頻道憑證密鑰
CHANNEL_ACCESS_TOKEN = 'line頻道憑證'
CHANNEL_SECRET = 'line頻道密鑰'

# 初始化 LineBot API 和 Webhook 處理程序
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 建立存取用戶資料 SQLite 資料庫
conn = sqlite3.connect('reminders.db', check_same_thread = False)
cursor = conn.cursor()

# 發送訊息給用戶
def send_message(user_id, message):
    line_bot_api.push_message(user_id, TextSendMessage(text = message))

# 檢查並運行安排好的提醒
def check_reminders():
    now = datetime.now().strftime("%H:%M")
    cursor.execute("SELECT user_id, type, name, times FROM reminders")
    reminders = cursor.fetchall()
    for reminder in reminders:
        user_id, rtype, name, times = reminder
        if rtype in ['med', 'supplement']:
            times_list = times.split(',')
            if now in times_list:
                cursor.execute("SELECT user_name, title FROM users WHERE user_id = ?", (user_id,))
                user_info = cursor.fetchone()
                user_name = user_info[0] if user_info else ""
                title = user_info[1] if user_info else ""
                if rtype == 'med':
                    send_message(user_id, f"{user_name} {title}，現在是您服用【{name}】的時間了。 \n \n 有病吃藥，沒病喝水，無聊看貓貓。")
                elif rtype == 'supplement':
                    send_message(user_id, f"{user_name} {title}，現在是您服用【{name}】的時間了。 \n \n 有病吃藥，沒病喝水，無聊看貓貓。")
                # 每隔5分鐘提醒一次，最多5次
                for i in range(1, 6):
                    schedule.every(5 * i).minutes.do(send_message, user_id, f"{user_name} {title}，現在是您服用【{name}】的時間了。 \n \n 有病吃藥，沒病喝水，無聊看貓貓。")
        elif rtype == 'water':
            frequency = int(times)
            start_time = datetime.now().replace(hour = 7, minute = 0, second = 0, microsecond = 0)  # 設定只會在 0700 ~ 1200 發送喝水提醒
            end_time = datetime.now().replace(hour = 0, minute = 0, second = 0, microsecond = 0) + timedelta(days = 1)
            current_time = datetime.now()
            if start_time <= current_time <= end_time:
                while start_time <= end_time:
                    if now == start_time.strftime("%H:%M"):
                        cursor.execute("SELECT user_name, title FROM users WHERE user_id = ?", (user_id,))
                        user_info = cursor.fetchone()
                        user_name = user_info[0] if user_info else ""
                        title = user_info[1] if user_info else ""
                        send_message(user_id, f"{user_name} {title}，現在是您該喝水的時間了。 \n \n 有病吃藥，沒病喝水，無聊看貓貓。")
                    start_time += timedelta(minutes = frequency)

# 每分鐘檢查是否有需要進行提醒的任務
schedule.every(1).minute.do(check_reminders)

# 處理來自 Line 的訊息
@app.route("/goodnightmiss", methods=['POST'])
def goodnightmiss():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理文字訊息，設定用戶吃藥/保健品、喝水和看貓貓的需求
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text
    if message_text == '吃藥':
        cursor.execute("UPDATE users SET pending_action = 'medication' WHERE user_id = ?", (user_id,))
        conn.commit()
        send_message(user_id, '請輸入藥物名稱：')
    elif message_text == '吃保健品':
        cursor.execute("UPDATE users SET pending_action = 'supplement' WHERE user_id = ?", (user_id,))
        conn.commit()
        send_message(user_id, '請輸入保健品名稱：')
    elif message_text == '喝水':
        cursor.execute("UPDATE users SET pending_action = 'water' WHERE user_id = ?", (user_id,))
        conn.commit()
        send_message(user_id, '請輸入每日飲水頻率（分鐘）：')
    elif message_text == '我要看貓貓':
        try:
            url = 'https://www.funnycatpix.com/'
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            imgs = soup.find_all('img')
            img_url = random.choice(imgs)['src']
            if not img_url.startswith('http'):
                img_url = url + img_url
            send_message(user_id, f"這是您的貓貓: {img_url}，要加油哦！")
        except Exception as e:
            send_message(user_id, f"無法取得貓貓圖片: {e}")
    elif message_text == 'ok':
        cursor.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
        conn.commit()
        send_message(user_id, "Yes, my lord. 不好意思打擾您了，已解除提醒。如有需要，請再次呼喚我。隨時候命，只待您的吩咐。")
    else:
        # 根據 pending_action 進行相應的處理
        cursor.execute("SELECT pending_action FROM users WHERE user_id = ?", (user_id,))
        pending_action = cursor.fetchone()
        if pending_action:
            pending_action = pending_action[0]
            if pending_action.startswith('medication:'):
                med_name = pending_action.split(':')[1]
                med_times = message_text
                cursor.execute("INSERT INTO reminders (user_id, type, name, times) VALUES (?, ?, ?, ?)", (user_id, 'med', med_name, med_times))
                conn.commit()
                send_message(user_id, f"已設定吃藥提醒：【{med_name}】 {med_times}")
                cursor.execute("UPDATE users SET pending_action = NULL WHERE user_id = ?", (user_id,))
                conn.commit()
            elif pending_action.startswith('supplement:'):
                supplement_name = pending_action.split(':')[1]
                supplement_times = message_text
                cursor.execute("INSERT INTO reminders (user_id, type, name, times) VALUES (?, ?, ?, ?)", (user_id, 'supplement', supplement_name, supplement_times))
                conn.commit()
                send_message(user_id, f"已設定吃保健品提醒：【{supplement_name}】 {supplement_times}")
                cursor.execute("UPDATE users SET pending_action = NULL WHERE user_id = ?", (user_id,))
                conn.commit()
            elif pending_action == 'water':
                water_frequency = message_text
                cursor.execute("INSERT INTO reminders (user_id, type, name, times) VALUES (?, ?, ?, ?)", (user_id, 'water', '喝水', water_frequency))
                conn.commit()
                send_message(user_id, f'已設定飲水提醒：每{water_frequency}分鐘')

# 啓動 Flask 應用程式
if __name__ == "__main__":
    app.run(debug = True)


