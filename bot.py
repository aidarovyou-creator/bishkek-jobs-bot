import telebot, json, os
from flask import Flask
import threading

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8115276999
CHANNEL_ID = "@Bishkek_Jobs_kg1"

CITIES = ["Бишкек", "Ош", "Баткен", "Жалал-Абад", "Каракол", "Нарын", "Талас", "Чүй"]
CATEGORIES = [("🚴 Курьер","Курьер"), ("☕ Официант","Официант"), ("🛒 Кассир","Кассир"), ("🧹 Тазалоочу","Тазалоочу"), ("📞 Call-центр","Call-центр"), ("💻 IT / SMM","IT / SMM"), ("📦 Башка","Башка")]

users = {}

def load_vacancies():
    try:
        with open("vacancies.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []
def save_vacancies(data):
    with open("vacancies.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def main_kb():
    m = telebot.types.InlineKeyboardMarkup(row_width=2)
    m.add(
        telebot.types.InlineKeyboardButton("🔍 Жумуш издөө", callback_data="search"),
        telebot.types.InlineKeyboardButton("📝 Вакансия кошуу", callback_data="add"),
        telebot.types.InlineKeyboardButton("🗑 Менин вакансиям", callback_data="my"),
        telebot.types.InlineKeyboardButton("ℹ️ Жардам", callback_data="help"),
    )
    return m

def cities_kb(prefix):
    m = telebot.types.InlineKeyboardMarkup(row_width=2)
    for c in CITIES:
        m.add(telebot.types.InlineKeyboardButton(f"📍 {c}", callback_data=f"{prefix}_city_{c}"))
    m.add(telebot.types.InlineKeyboardButton("🔙 Артка", callback_data="home"))
    return m

def cats_kb(prefix):
    m = telebot.types.InlineKeyboardMarkup(row_width=2)
    for emoji_name, name in CATEGORIES:
        m.add(telebot.types.InlineKeyboardButton(emoji_name, callback_data=f"{prefix}_cat_{name}"))
    m.add(telebot.types.InlineKeyboardButton("🔙 Артка", callback_data="home"))
    return m

def vacancy_card(v):
    text = f"💼 <b>{v['title']}</b>\n\n🏙 Шаар: {v['city']}\n📂 Категория: {v['category']}\n💰 Айлык: <b>{v['salary']} сом</b>\n📝 {v['desc']}"
    m = telebot.types.InlineKeyboardMarkup()
    phone = str(v['phone']).replace(" ", "").replace("+", "")
    if phone.startswith("0"):
        phone = "996" + phone[1:]
    m.add(telebot.types.InlineKeyboardButton("📞 Байланыш", url=f"https://t.me/+{phone}" if False else f"tel:+{phone}"))
    # Telegramда телефонго түз шилтеме болбойт, ошондуктан номерди текстке да чыгарабыз
    text += f"\n📞 Байланыш: <code>{v['phone']}</code>"
    return text, m

@bot.message_handler(commands=['start'])
def start(message):
    all_users = load_users()
    if message.chat.id not in [u["id"] for u in all_users]:
        all_users.append({"id": message.chat.id, "name": message.from_user.first_name, "username": message.from_user.username})
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(all_users, f, ensure_ascii=False, indent=2)
    bot.send_message(message.chat.id, "👋 <b>Салам! Мен - Жумуш Ботумун.</b>\n\n🇰🇬 Кыргызстан боюнча эң оңой жумуш издөө!\n\nТөмөндөн танда 👇", reply_markup=main_kb(), parse_mode="HTML")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.chat.id != ADMIN_ID:
        return
    all_users = load_users()
    vacancies = load_vacancies()
    text = f"📊 <b>СТАТИСТИКА</b>\n\n👥 Адам: {len(all_users)}\n📝 Вакансия: {len(vacancies)}\n\n🆕 Акыркы адамдар:\n"
    for u in all_users[-10:]:
        text += f"- {u.get('name')} @{u.get('username')}\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    if data == "home":
        users.pop(chat_id, None)
        bot.edit_message_text("🏠 <b>Башкы меню</b>\n\nТанда 👇", chat_id, call.message.message_id, reply_markup=main_kb(), parse_mode="HTML")
        return

    if data == "help":
        bot.edit_message_text("ℹ️ <b>КАНТИП КОЛДОНСОҢ?</b>\n\n🔍 <b>Жумуш издөө:</b> Шаар → Категория → Даяр! Вакансиялар карточка болуп чыгат.\n\n📝 <b>Вакансия кошуу:</b> Шаар → Категория → Аты → Айлык → Телефон → Сүрөттөмө. Болду! Админ текшерип, каналга чыгарат.\n\n🗑 <b>Өчүрүү:</b> Өзүңдүн вакансияңды өзүң өчүрө аласың.\n\n❓ Суроо болсо - @bishkek_jobs_kg_bot ка жаз.", chat_id, call.message.message_id, reply_markup=main_kb(), parse_mode="HTML")
        return

    if data == "search":
        users[chat_id] = {"step": "search_city"}
        bot.edit_message_text("📍 <b>Кайсы шаардан издейсиң?</b>", chat_id, call.message.message_id, reply_markup=cities_kb("search"), parse_mode="HTML")
        return

    if data == "add":
        users[chat_id] = {"step": "add_city"}
        bot.edit_message_text("📍 <b>Вакансия кайсы шаарда?</b>", chat_id, call.message.message_id, reply_markup=cities_kb("add"), parse_mode="HTML")
        return

    if data == "my":
        vacancies = load_vacancies()
        my = [(i, v) for i, v in enumerate(vacancies) if v["user_id"] == chat_id]
        if not my:
            bot.edit_message_text("😔 Сенин азырынча вакансияң жок.", chat_id, call.message.message_id, reply_markup=main_kb())
            return
        m = telebot.types.InlineKeyboardMarkup()
        for i, v in my:
            m.add(telebot.types.InlineKeyboardButton(f"🗑 {v['title']} - {v['city']}", callback_data=f"del_{i}"))
        m.add(telebot.types.InlineKeyboardButton("🔙 Артка", callback_data="home"))
        bot.edit_message_text("🗑 <b>Өчүргүң келгенди бас:</b>", chat_id, call.message.message_id, reply_markup=m, parse_mode="HTML")
        return

    if data.startswith("del_"):
        try:
            idx = int(data.replace("del_", ""))
            vacancies = load_vacancies()
            deleted = vacancies.pop(idx)
            save_vacancies(vacancies)
            bot.edit_message_text(f"✅ Өчүрүлдү: {deleted['title']}", chat_id, call.message.message_id, reply_markup=main_kb())
        except:
            bot.edit_message_text("Ката кетти.", chat_id, call.message.message_id, reply_markup=main_kb())
        return

    if data.startswith("search_city_"):
        city = data.replace("search_city_", "")
        users[chat_id] = {"step": "search_cat", "city": city}
        bot.edit_message_text(f"📍 {city}\n\n📂 <b>Категорияны танда:</b>", chat_id, call.message.message_id, reply_markup=cats_kb("search"), parse_mode="HTML")
        return

    if data.startswith("search_cat_"):
        cat = data.replace("search_cat_", "")
        city = users.get(chat_id, {}).get("city", "")
        vacancies = load_vacancies()
        found = [v for v in vacancies if v["city"] == city and v["category"] == cat]
        if not found:
            bot.edit_message_text(f"😔 {city} - {cat} боюнча азырынча вакансия жок.\n\nКийин кайра кирип көр.", chat_id, call.message.message_id, reply_markup=main_kb())
            return
        bot.edit_message_text(f"✅ {city} - {cat} боюнча {len(found)} вакансия табылды 👇", chat_id, call.message.message_id, reply_markup=main_kb())
        for v in found:
            text, kb = vacancy_card(v)
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
        users.pop(chat_id, None)
        return

    if data.startswith("add_city_"):
        city = data.replace("add_city_", "")
        users[chat_id] = {"step": "add_cat", "city": city}
        bot.edit_message_text(f"📍 {city}\n\n📂 <b>Категорияны танда:</b>", chat_id, call.message.message_id, reply_markup=cats_kb("add"), parse_mode="HTML")
        return

    if data.startswith("add_cat_"):
        cat = data.replace("add_cat_", "")
        st = users.get(chat_id, {})
        st["category"] = cat
        st["step"] = "title"
        users[chat_id] = st
        bot.send_message(chat_id, "✏️ <b>Вакансиянын атын жаз:</b>\nМисалы: Курьер керек", parse_mode="HTML")
        return

@bot.message_handler(func=lambda m: True)
def texts(message):
    chat_id = message.chat.id
    st = users.get(chat_id)
    if not st:
        bot.send_message(chat_id, "Менюдан танда 👇", reply_markup=main_kb())
        return
    step = st.get("step")
    txt = message.text or ""

    if step == "title":
        st["title"] = txt
        st["step"] = "salary"
        bot.send_message(chat_id, "💰 <b>Айлыгы канча?</b>\nМисалы: 45000", parse_mode="HTML")
        return
    if step == "salary":
        st["salary"] = txt
        st["step"] = "phone"
        bot.send_message(chat_id, "📞 <b>Телефонуңду жаз:</b>\nМисалы: 0700123456", parse_mode="HTML")
        return
    if step == "phone":
        st["phone"] = txt
        st["step"] = "desc"
        bot.send_message(chat_id, "📝 <b>Кыскача жаз:</b>\nМисалы: Күнүнө 8 саат, тамак берилет", parse_mode="HTML")
        return
    if step == "desc":
        vacancies = load_vacancies()
        new_v = {"user_id": chat_id, "city": st["city"], "category": st["category"], "title": st["title"], "salary": st["salary"], "phone": st["phone"], "desc": txt}
        vacancies.append(new_v)
        save_vacancies(vacancies)
        users.pop(chat_id, None)
        bot.send_message(chat_id, "✅ <b>Вакансия кабыл алынды!</b>\n\nАдмин текшерип, каналга чыгарат. Рахмат!", reply_markup=main_kb(), parse_mode="HTML")
        # Админге билдирүү
        try:
            bot.send_message(ADMIN_ID, f"🆕 ЖАҢЫ ВАКАНСИЯ (текшерүү керек)\n\n💼 {new_v['title']}\n🏙 {new_v['city']} | {new_v['category']}\n💰 {new_v['salary']}\n📞 {new_v['phone']}\n📝 {new_v['desc']}\n\nКаналга чыгаруу үчүн өзүң чыгарып кой.")
        except:
            pass
        # Каналга дароо чыгаруу
        try:
            channel_text = f"💼 <b>ЖАҢЫ ВАКАНСИЯ!</b>\n\n💼 {new_v['title']}\n🏙 Шаар: {new_v['city']}\n📂 Категория: {new_v['category']}\n💰 Айлык: <b>{new_v['salary']} сом</b>\n📞 Байланыш: <code>{new_v['phone']}</code>\n📝 {new_v['desc']}\n\n👇 Бардык вакансиялар:\n@bishkek_jobs_kg_bot"
            bot.send_message(CHANNEL_ID, channel_text, parse_mode="HTML")
        except Exception as e:
            print(f"Каналга чыгарууда ката: {e}")
        return

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot ishтеп жатат! V5"

def run_bot():
    print("Бот иштеп жатат... V5 - Inline")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
