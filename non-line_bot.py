import requests
from bs4 import BeautifulSoup
import schedule
import time
import threading
import sqlite3
from datetime import datetime, timedelta
import random

# 建立用戶資料庫
conn = sqlite3.connect('reminders.db', check_same_thread = False)
cursor = conn.cursor()

# 刪除原有資料表
cursor.execute('DROP TABLE IF EXISTS reminders')
cursor.execute('DROP TABLE IF EXISTS users')

# 重新創建資料表
cursor.execute('''
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    type TEXT,
    name TEXT,
    times TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    user_name TEXT,
    title TEXT
)
''')

# 主程式架構：收集用戶名字稱呼、藥物/保健品名稱與服用時間、喝水時間頻率、發送貓貓圖網路爬蟲設定
def main():
    user_id = "test_user"

    # 一開始先發送使用説明的訊息
    send_message(user_id, """"呀咧呀咧，大小姐/大少爺 , It's time to~~~~~ \n \n 就讓「有病要吃藥、沒事多喝水、心累看貓貓」——關心你生心理需求多功能提醒 Line Bot陪伴您。
                                您可輸入「？」或「help」查看使用説明。\n \n
                                【使用説明】
                                ·輸入「我的名字是」可設定名字。
                                ·輸入「稱呼我大小姐」或「稱呼我大少爺」可設定稱呼。
                                ·輸入「吃藥」進入「吃藥」提醒設定畫面。
                                ·輸入「吃保健品」進入「吃保健品」提醒設定畫面。
                                ·輸入「喝水」進入「喝水」提醒設定畫面。
                                ·輸入「我要看貓貓」即可獲得隨機療愈貓貓照片。
                                ·到您所設定的提醒時間後，我會每分鐘連續傳5次訊息提醒您，直到您輸入「ok」後才會停止傳送提醒訊息。""")
    while True:
        mtext = input ("請輸入想要執行的指令~")

        if mtext == 'help' or mtext == '?':
            print ("""
                    【使用説明】
                    ·輸入「我的名字是」可設定名字。
                    ·輸入「稱呼我大小姐」或「稱呼我大少爺」可設定稱呼。
                    ·輸入「吃藥」進入「吃藥」提醒設定畫面。
                    ·輸入「吃保健品」進入「吃保健品」提醒設定畫面。
                    ·輸入「喝水」進入「喝水」提醒設定畫面。
                    ·輸入「我要看貓貓」即可獲得隨機療愈貓貓照片。
                    ·到您所設定的提醒時間後，我會每分鐘連續傳5次訊息提醒您，直到您輸入「ok」後才會停止傳送提醒訊息。
                   """)

        elif mtext.startswith('我的名字是 '):
            user_name = mtext.split(' ')[1]
            cursor.execute("INSERT OR REPLACE INTO users (user_id, user_name, title) VALUES (?, ?, ?)", (user_id, user_name, None))
            conn.commit()
            print(f'名字已設定為：{user_name}')  # 加入這行來顯示設定成功的訊息

        elif mtext == '稱呼我大小姐':
            cursor.execute("UPDATE users SET title = '大小姐' WHERE user_id = ?", (user_id,))
            conn.commit()
            print('稱呼已設定為：大小姐')

        elif mtext == '稱呼我大少爺':
            cursor.execute("UPDATE users SET title = '大少爺' WHERE user_id = ?", (user_id,))
            conn.commit()
            print('稱呼已設定為：大少爺')

        elif mtext == '吃藥':
            med_name = input('請輸入藥物名稱：')
            med_times = input('請輸入服用時間（24小時制，使用逗號分隔多個時間）：')
            cursor.execute("INSERT INTO reminders (user_id, type, name, times) VALUES (?, ?, ?, ?)", (user_id, 'med', med_name, med_times))
            conn.commit()
            print(f"已設定吃藥提醒：【{med_name}】 {med_times}")

        elif mtext == '吃保健品':
            supplement_name = input('請輸入保健品名稱：')
            supplement_times = input('請輸入服用時間（24小時制(21:00)，使用逗號分隔多個時間）：')
            cursor.execute("INSERT INTO reminders (user_id, type, name, times) VALUES (?, ?, ?, ?)", (user_id, 'supplement', supplement_name, supplement_times))
            conn.commit()
            print(f"已設定吃保健品提醒：【{supplement_name}】 {supplement_times}")

        elif mtext == '喝水':
            water_frequency = input('請輸入每日飲水頻率（分鐘）：')
            cursor.execute("INSERT INTO reminders (user_id, type, name, times) VALUES (?, ?, ?, ?)", (user_id, 'water', '喝水', water_frequency))
            conn.commit()
            print(f'已設定飲水提醒：每{water_frequency}分鐘')

        elif mtext == '我要看貓貓':
            try:
                url = 'https://www.funnycatpix.com/'
                r = requests.get(url)
                soup = BeautifulSoup(r.text, "html.parser")
                imgs = soup.find_all('img')
                img_url = random.choice(imgs)['src']
                if not img_url.startswith('http'):
                    img_url = url + img_url
                print(f"這是你的貓貓: {img_url}，要加油哦！")
            except Exception as e:
                print(f"無法取得貓貓圖片: {e}")

        elif mtext == 'ok':
            print("Yes, my lord. 不好意思打擾您了，已解除提醒。如有需要，請再次呼喚我。隨時候命，只待您的吩咐。")

# 發送提醒訊息
def send_message(user_id, message):
    print(f"To {user_id}: {message}")

# 檢查和運行安排好的定時提醒
def schedule_jobs():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 啓動定時提醒的運行thread，讓多個運行thread同時運行
threading.Thread(target = schedule_jobs).start()

# 設定用戶各項定時提醒的内容
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
                    send_message(user_id, f"{user_name} {title}, 現在是您用【{name}】的時間了。 \n \n 有病吃藥，沒病喝水，沒事看貓貓。")
                elif rtype == 'supplement':
                    send_message (user_id, f"{user_name} {title}, 現在是您用【{name}】的時間了。 \n \n 有病吃藥，沒病喝水，沒事看貓貓。")
                # 每隔5分鐘提醒一次
                for i in range(1, 6):
                    schedule.every(5 * i).minutes.do (send_message, user_id, f"{user_name} {title}, 現在是您用【{name}】的時間了。 \n \n 有病吃藥，沒病喝水，沒事看貓貓。")
        elif rtype == 'water':
            frequency = int(times)
            start_time = datetime.now().replace (hour = 7, minute = 0, second = 0, microsecond = 0)   #設定只會在 0700 ~ 1200發送喝水提醒
            end_time = datetime.now().replace (hour = 0, minute = 0, second = 0, microsecond = 0) + timedelta (days = 1)
            current_time = datetime.now()
            if start_time <= current_time <= end_time:
                while start_time <= end_time:
                    if now == start_time.strftime("%H:%M"):
                        cursor.execute("SELECT user_name, title FROM users WHERE user_id = ?", (user_id,))
                        user_info = cursor.fetchone()
                        user_name = user_info[0] if user_info else ""
                        title = user_info[1] if user_info else ""
                        send_message(user_id, f"{user_name} {title}, 現在是您該喝水的時間了。 \n \n 有病吃藥，沒病喝水，沒事看貓貓。")
                    start_time += timedelta(minutes = frequency)

# 每分鐘檢查是否有需要進行提醒的任務
schedule.every(1).minute.do(check_reminders)

if __name__ == '__main__':
    main()
