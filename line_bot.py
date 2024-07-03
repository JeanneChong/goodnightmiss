import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import schedule
import time
import threading
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)

# LINE Bot credentials
line_bot_api = LineBotApi('ZuqEf8yqUPeYP0Ekr9Q3tiv0fy5MVa7MUa9m/BuM9e1M3VBHRBEUjdSIz+Fesg+lzzqz05VbZTasXaWpDwcc3sJi10gft4S9cSMHDQ79jAum51T3qUPwrRzLIiugzovRQceNJ4ro67sVmtihY9lUUAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('3b121dfe3eadcd614bd6bd10cb18f0ca')

# Database setup
conn = sqlite3.connect('reminders.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, user_id TEXT, type TEXT, name TEXT, time TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, user_name TEXT, title TEXT)''')
conn.commit()

# Helper function to send a message
def send_message(user_id, message):
    line_bot_api.push_message(user_id, TextSendMessage(text=message))

# Schedule jobs
def schedule_jobs():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=schedule_jobs).start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    mtext = event.message.text

    if mtext == 'help' or mtext == '?':
        try:
            message = TextSendMessage(
                text="Line bot 功能説明： \n \n 1.提醒吃藥功能：用戶可以輸入每日需要服用的藥物名稱，並設定提醒的頻率。Line bot會在設定的時間提醒用戶服用藥物。\n \n 2.提醒吃保健品功能：用戶可以輸入每日需要服用的保健品名稱，並設定提醒的頻率。Line bot會在設定的時間提醒用戶服用保健品。\n \n 3.提醒喝水功能：用戶可以輸入每日需要攝入的水量，並設定喝水的時間頻率。Line bot會自動計算每次需要喝的水量，並在設定的時間提醒用戶喝水。\n \n 4.自動提供可愛貓貓圖：用戶可以設定每日需要獲得可愛貓貓圖的頻率，Line bot會自動按照設定的時間推送貓貓圖並附上加油打氣的話語。"
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
            line_bot_api.reply_message(event.reply_token,
                                      TextSendMessage(text='呀咧呀咧~'))
    elif mtext.startswith('我的名字是 '):
        user_name = mtext.split(' ')[1]
        cursor.execute("INSERT OR REPLACE INTO users (user_id, user_name, title) VALUES (?, ?, ?)", (user_id, user_name, None))
        conn.commit()
        message = TextSendMessage(text=f'名字已設定為：{user_name}')
        line_bot_api.reply_message(event.reply_token, message)
    elif mtext == '稱呼我大小姐':
        cursor.execute("UPDATE users SET title = '大小姐' WHERE user_id = ?", (user_id,))
        conn.commit()
        message = TextSendMessage(text='稱呼已設定為：大小姐')
        line_bot_api.reply_message(event.reply_token, message)
    elif mtext == '稱呼我大少爺':
        cursor.execute("UPDATE users SET title = '大少爺' WHERE user_id = ?", (user_id,))
        conn.commit()
        message = TextSendMessage(text='稱呼已設定為：大少爺')
        line_bot_api.reply_message(event.reply_token, message)
    elif mtext == '@吃藥':
        try:
            message = TextSendMessage(
                text='請問您服用的藥名是？'
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
            line_bot_api.reply_message(event.reply_token,
                                      TextSendMessage(text='呀咧呀咧~您再不吃藥我要跳舞了'))
    elif mtext.startswith('@吃藥 '):
        med_name = mtext.split(' ')[1]
        cursor.execute("INSERT INTO reminders (user_id, type, name, time) VALUES (?, ?, ?, ?)", (user_id, 'med', med_name, datetime.now().strftime("%H:%M:%S")))
        conn.commit()
        message = TextSendMessage(text=f'已設定吃藥提醒：{med_name}')
        line_bot_api.reply_message(event.reply_token, message)
    elif mtext == '@吃保健品':
        try:
            message = TextSendMessage(
                text='請問您服用的保健品名稱是？'
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
            line_bot_api.reply_message(event.reply_token,
                                      TextSendMessage(text='呀咧呀咧~您再不吃保健品我要跳舞了'))
    elif mtext.startswith('@吃保健品 '):
        supplement_name = mtext.split(' ')[1]
        cursor.execute("INSERT INTO reminders (user_id, type, name, time) VALUES (?, ?, ?, ?)", (user_id, 'supplement', supplement_name, datetime.now().strftime("%H:%M:%S")))
        conn.commit()
        message = TextSendMessage(text=f'已設定吃保健品提醒：{supplement_name}')
        line_bot_api.reply_message(event.reply_token, message)
    elif mtext == '@喝水':
        try:
            message = TextSendMessage(
                text='請問您的目標飲水量是多少？'
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
            line_bot_api.reply_message(event.reply_token,
                                      TextSendMessage(text='呀咧呀咧~您再不喝水我要跳舞了'))
    elif mtext.startswith('@喝水 '):
        water_amount = mtext.split(' ')[1]
        cursor.execute("INSERT INTO reminders (user_id, type, name, time) VALUES (?, ?, ?, ?)", (user_id, 'water', water_amount, datetime.now().strftime("%H:%M:%S")))
        conn.commit()
        message = TextSendMessage(text=f'已設定喝水提醒：{water_amount} 毫升')
        line_bot_api.reply_message(event.reply_token, message)
    elif mtext == '@我要看貓貓':
        try:
            url = 'https://www.funnycatpix.com/'
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            imgs = soup.find_all('img')
            img_url = random.choice(imgs)['src']
            if not img_url.startswith('http'):
                img_url = url + img_url
            message = ImageSendMessage(
                original_content_url=img_url,
                preview_image_url=img_url
            )
            line_bot_api.reply_message(event.reply_token, message)
        except:
            line_bot_api.reply_message(event.reply_token,
                                      TextSendMessage(text='喵喵喵'))

    # 發送預設訊息
    else:
        default_message = TextSendMessage(
            text="呀咧呀咧，早安午安晚安大小姐/大少爺様, It's time to~~~~~\n\n就讓「有病要吃藥、沒事多喝水、心累看貓貓」——關心你生心理需求多功能提醒 Line Bot陪伴您。\n您可輸入「？」或「help」查看使用説明。輸入「@吃藥」「@吃保健品」「@喝水」「@我要看貓貓」。\n\n輸入「我的名字是 你的名字」來設定您的名字，並輸入「稱呼我大小姐」或「稱呼我大少爺」來設定您的稱呼。"
        )
        line_bot_api.reply_message(event.reply_token, default_message)

# 定时任务
def check_reminders():
    now = datetime.now().strftime("%H:%M:%S")
    cursor.execute("SELECT user_id, type, name FROM reminders WHERE time=?", (now,))
    reminders = cursor.fetchall()
    for reminder in reminders:
        user_id, rtype, name = reminder
        cursor.execute("SELECT user_name, title FROM users WHERE user_id=?", (user_id,))
        user_info = cursor.fetchone()
        user_name = user_info[0] if user_info else ""
        title = user_info[1] if user_info else ""
        if rtype == 'med':
            send_message(user_id, f"{user_name}{title}, 提醒：該吃藥了 {name}")
        elif rtype == 'supplement':
            send_message(user_id, f"{user_name}{title}, 提醒：該吃保健品了 {name}")
        elif rtype == 'water':
            send_message(user_id, f"{user_name}{title}, 提醒：該喝水了 {name} 毫升")

schedule.every().minute.do(check_reminders)

if __name__ == '__main__':
    app.run()

