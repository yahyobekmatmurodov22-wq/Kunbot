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

# === Asosiy menyu ===
def main_menu(chat_id, text="👋 Asosiy menyu"):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Vazifa qo‘shish", "📋 Vazifalarim")
    if bot.get_chat(chat_id).username == ADMIN_USERNAME.replace("@", ""):
        kb.row("🛠 Admin panel")
    bot.send_message(chat_id, text, reply_markup=kb)

# === /start komandasi ===
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
        datetime.strptime(task_time, "%H:%M")  # vaqt formati tekshiruvi

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
    kb = types.InlineKeyboardMarkup()
    for i, t in enumerate(data[user_id]):
        text += f"{i+1}. {t['text']} — {t['time']}\n"
        kb.add(types.InlineKeyboardButton(f"❌ O‘chirish {i+1}", callback_data=f"del_{i}"))
    bot.send_message(msg.chat.id, text, reply_markup=kb)

# === Vazifani o‘chirish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def delete_task(call):
    index = int(call.data.split("_")[1])
    data = load_tasks()
    user_id = str(call.message.chat.id)
    if user_id in data and 0 <= index < len(data[user_id]):
        del data[user_id][index]
        save_tasks(data)
        bot.answer_callback_query(call.id, "🗑 Vazifa o‘chirildi!")
        bot.edit_message_text("✅ Vazifa o‘chirildi!", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Xatolik!")

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
    foydalanuvchilar = list(data.keys())
    yuborilgan = 0
    for user_id in foydalanuvchilar:
        try:
            bot.send_message(int(user_id), f"📢 {text}")
            yuborilgan += 1
        except:
            pass
    bot.send_message(msg.chat.id, f"✅ Reklama {yuborilgan} foydalanuvchiga yuborildi!")

# === Har daqiqa eslatma tekshiruvi ===
def reminder_loop():
    while True:
        now = datetime.now().strftime("%H:%M")
        data = load_tasks()
        for user_id, vazifalar in data.items():
            for t in vazifalar:
                if t["time"] == now:
                    try:
                        bot.send_message(int(user_id), f"⏰ Eslatma!\n'{t['text']}' vaqti keldi!")
                    except:
                        pass
        time.sleep(60)  # 1 daqiqa oraliq

threading.Thread(target=reminder_loop, daemon=True).start()

# === Flask server (Render uchun) ===
@app.route("/")
def home():
    return "🤖 Bot ishlayapti!"

if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()
    bot.polling(none_stop=True)
        
