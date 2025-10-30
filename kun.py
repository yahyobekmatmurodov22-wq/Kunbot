import telebot
from telebot import types
import datetime, threading, time
from flask import Flask
import os

TOKEN = "8207865664:AAFxHA8WlZl6d2LDv46zToeDE-9DhpLXSGE"
ADMIN_USERNAME = "yahyobek_04_26"  # <-- username orqali adminlik

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

tasks = {}

# --- FONDA ESLATMA TEKSHIRISH ---
def reminder_loop():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for user_id in list(tasks.keys()):
            for task in tasks[user_id][:]:
                if task["time"] == now:
                    bot.send_message(user_id, f"⏰ *Eslatma vaqti keldi!*\n📋 {task['text']}", parse_mode="Markdown")
                    tasks[user_id].remove(task)
        time.sleep(30)

threading.Thread(target=reminder_loop, daemon=True).start()

# --- START ---
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.chat.id
    if user_id not in tasks:
        tasks[user_id] = []
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Eslatma qo‘shish", "📋 Eslatmalar", "👑 Admin panel")
    bot.send_message(user_id, "👋 Assalomu alaykum! Men *Kun Tartibi Bot*man.\n\n📅 Vaqtingizni rejalashtiring!", parse_mode="Markdown", reply_markup=markup)

# --- ESLATMA QO‘SHISH ---
@bot.message_handler(func=lambda m: m.text == "➕ Eslatma qo‘shish")
def add_task(msg):
    bot.send_message(msg.chat.id, "✍️ Eslatma matnini kiriting:")
    bot.register_next_step_handler(msg, get_task_text)

def get_task_text(msg):
    text = msg.text
    bot.send_message(msg.chat.id, "⌚ Vaqtni `HH:MM` formatda kiriting (masalan, 07:30):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, get_task_time, text)

def get_task_time(msg, text):
    try:
        datetime.datetime.strptime(msg.text, "%H:%M")
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Noto‘g‘ri format. Qaytadan kiriting (masalan: 08:45)")
        return
    user_id = msg.chat.id
    tasks[user_id].append({"text": text, "time": msg.text})
    bot.send_message(user_id, f"✅ Eslatma qo‘shildi!\n🕒 {msg.text} – {text}")

# --- ESLATMALAR RO‘YXATI ---
@bot.message_handler(func=lambda m: m.text == "📋 Eslatmalar")
def show_tasks(msg):
    user_id = msg.chat.id
    if user_id not in tasks or not tasks[user_id]:
        bot.send_message(user_id, "📭 Sizda hozircha eslatma yo‘q.")
        return
    for i, t in enumerate(tasks[user_id]):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ O‘chirish", callback_data=f"del_{i}"))
        bot.send_message(user_id, f"🕒 {t['time']} – {t['text']}", reply_markup=markup)

# --- ESLATMANI O‘CHIRISH ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def delete_task(call):
    user_id = call.message.chat.id
    index = int(call.data.split("_")[1])
    try:
        deleted = tasks[user_id].pop(index)
        bot.edit_message_text(f"🗑 O‘chirildi: {deleted['text']}", user_id, call.message.message_id)
    except:
        bot.answer_callback_query(call.id, "❌ Allaqachon o‘chirilgan.")

# --- ADMIN PANEL ---
@bot.message_handler(func=lambda m: m.text == "👑 Admin panel")
def admin_panel(msg):
    if msg.from_user.username != ADMIN_USERNAME:
        bot.send_message(msg.chat.id, "❌ Siz admin emassiz.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📢 Reklama yuborish", "🔙 Orqaga")
    bot.send_message(msg.chat.id, "👑 Admin panelga xush kelibsiz!", reply_markup=markup)

# --- REKLAMA YUBORISH ---
@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish" and m.from_user.username == ADMIN_USERNAME)
def reklama_1(msg):
    bot.send_message(msg.chat.id, "✍️ Reklama matnini yuboring:")
    bot.register_next_step_handler(msg, reklama_send)

def reklama_send(msg):
    ad_text = msg.text
    count = 0
    for user_id in tasks.keys():
        try:
            bot.send_message(user_id, f"📢 *Reklama:*\n{ad_text}", parse_mode="Markdown")
            count += 1
        except:
            pass
    bot.send_message(msg.chat.id, f"✅ Reklama {count} foydalanuvchiga yuborildi.")

# --- ORQAGA QAYTISH ---
@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def back(msg):
    start(msg)

# --- RENDER UCHUN PORT ---
@app.route('/')
def home():
    return "Kun Tartibi Bot ishlayapti!"

port = int(os.environ.get("PORT", 8080))
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()

print("✅ Kun Tartibi Bot ishga tushdi!")
bot.polling(none_stop=True)
