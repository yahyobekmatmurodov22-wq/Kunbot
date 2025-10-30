import telebot
import json
import os
import time
import threading
from telebot import types
from flask import Flask
from datetime import datetime

# === Sozlamalar ===
BOT_TOKEN = "8207865664:AAFxHA8WlZl6d2LDv46zToeDE-9DhpLXSGE"
ADMIN_USERNAME = "@yahyobek_04_26"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

DATA_FILE = "tasks.json"

# === Fayl yaratish ===
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# === JSON o‘qish / yozish ===
def load_tasks():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_tasks(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# === Bosh menyu ===
def main_menu(chat_id, text="👋 Asosiy menyu"):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Vazifa qo‘shish", "📋 Vazifalarim")
    if ADMIN_USERNAME.replace("@", "") == bot.get_chat(chat_id).username:
        kb.row("🛠 Admin panel")
    bot.send_message(chat_id, text, reply_markup=kb)

# === Start komandasi ===
@bot.message_handler(commands=["start"])
def start(msg):
    data = load_tasks()
    user_id = str(msg.chat.id)
    if user_id not in data:
        data[user_id] = []
        save_tasks(data)
    main_menu(msg.chat.id, "👋 Salom! Men sizga kun tartibingizni eslatib turaman!")

# === Vazifa qo‘shish ===
@bot.message_handler(func=lambda m: m.text == "➕ Vazifa qo‘shish")
def add_task(msg):
    bot.send_message(msg.chat.id, "📝 Vazifani kiriting:\nMasalan: *Ingliz tili - 15:30*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_task_step)

def save_task_step(msg):
    text = msg.text
    try:
        if "-" not in text:
            bot.send_message(msg.chat.id, "❌ Format noto‘g‘ri. Masalan: 'Matematika - 18:30'")
            return
        task_text, task_time = text.split("-")
        task_text = task_text.strip()
        task_time = task_time.strip()
        datetime.strptime(task_time, "%H:%M")  # vaqt formati

        data = load_tasks()
        user_id = str(msg.chat.id)
        if user_id not in data:
            data[user_id] = []

        data[user_id].append({
            "text": task_text,
            "time": task_time
        })
        save_tasks(data)

        bot.send_message(msg.chat.id, f"✅ Saqlandi!\n📌 {task_text} — {task_time}")
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Xato: {e}")

# === Vazifalar ro‘yxati ===
@bot.message_handler(func=lambda m: m.text == "📋 Vazifalarim")
def show_tasks(msg):
    data = load_tasks()
    user_id = str(msg.chat.id)
    if user_id not in data or len(data[user_id]) == 0:
        bot.send_message(msg.chat.id, "📭 Sizda hozircha vazifa yo‘q.")
        return

    text = "🗓 Sizning vazifalaringiz:\n\n"
    for t in data[user_id]:
        text += f"- {t['text']} ({t['time']})\n"
    bot.send_message(msg.chat.id, text)

# === Admin panel ===
@bot.message_handler(func=lambda m: m.text == "🛠 Admin panel")
def admin_panel(msg):
    if msg.from_user.username != ADMIN_USERNAME.replace("@", ""):
        bot.send_message(msg.chat.id, "⛔ Siz admin emassiz.")
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📢 Reklama yuborish", "⬅️ Orqaga")
    bot.send_message(msg.chat.id, "🧰 Admin panel:", reply_markup=kb)

# === Orqaga tugmasi ===
@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def back_to_menu(msg):
    main_menu(msg.chat.id, "⬅️ Asosiy menyuga qaytdingiz.")

# === Reklama yuborish ===
@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish")
def reklama_boshlash(msg):
    if msg.from_user.username != ADMIN_USERNAME.replace("@", ""):
        return
    bot.send_message(msg.chat.id, "✍️ Reklama matnini kiriting:")
    bot.register_next_step_handler(msg, reklama_yuborish)

def reklama_yuborish(msg):
    if msg.from_user.username != ADMIN_USERNAME.replace("@", ""):
        return
    text = msg.text
    data = load_tasks()
    userlar = list(data.keys())
    yuborilgan = 0
    for user_id in userlar:
        try:
            bot.send_message(int(user_id), f"📢 {text}")
            yuborilgan += 1
        except:
            pass
    bot.send_message(msg.chat.id, f"✅ Reklama {yuborilgan} foydalanuvchiga yuborildi!")

# === Har kuni avtomatik eslatma ===
def reminder_loop():
    while True:
        now = datetime.now().strftime("%H:%M")
        data = load_tasks()
        for user_id, tasks in data.items():
            for t in tasks:
                if t["time"] == now:
                    try:
                        bot.send_message(int(user_id), f"⏰ Eslatma!\n{t['text']} vaqti keldi!")
                    except:
                        pass
        time.sleep(60)  # 1 daqiqada tekshiriladi

threading.Thread(target=reminder_loop, daemon=True).start()

# === Flask server (Render uchun) ===
@app.route("/")
def home():
    return "🤖 Bot ishlayapti!"

if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()
    bot.polling(none_stop=True)