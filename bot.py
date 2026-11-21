import telebot, json, os, requests
from flask import Flask
import threading

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8115276999
CHANNEL_ID = "@Bishkek_Jobs_kg1"
CHANNEL_URL = "https://t.me/Bishkek_Jobs_kg1"
NPOINT_ID = os.environ.get("NPOINT_ID")
NPOINT_URL = f"https://api.npoint.io/{NPOINT_ID}" if NPOINT_ID else None

CITIES = ["Бишкек", "Ош", "Баткен", "Жалал-Абад", "Каракол", "Нарын", "Талас", "Чүй"]
CATEGORIES = [("🚴 Курьер","Курьер"), ("☕ Официант","Официант"), ("🛒 Кассир","Кассир"), ("🧹 Тазалоочу","Тазалоочу"), ("📞 Call-центр","Call-центр"), ("💻 IT / SMM","IT / SMM"), ("📦 Башка","Башка")]

users = {}

def load_data():
    if NPOINT_URL:
        try:
            r = requests.get(NPOINT_URL, timeout=10)
            if r.status_code == 200:
                d = r.json()
                if "vacancies" in d:
                    return d
        except Exception as e:
            print(f"Окуу ката: {e}")
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"vacancies": [], "users": []}

def save_data(data):
    # Адегенде файлга сактайбыз - дароо иштесин
    try:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass
    if NPOINT_URL:
        try:
            requests.post(NPOINT_URL, json=data, timeout=10)
        except Exception as e:
            print(f"Жазуу ката: {e}")

def load_vacancies():
    return load_data().get("vacancies", [])

# --- АСТЫНДАГЫ ТУРУКТУУ КНОПКАЛАР ---
def bottom_kb():
    m = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add("🔍 Жумуш издөө", "📝 Вакансия кошуу")
    m.add("📢 Канал", "ℹ️ Жардам")
    m.add("🔄 Старт")
    return m

def main_inline():
    m = telebot.types.InlineKeyboardMarkup(row_width=2)
    m.add(
        telebot.types.InlineKeyboardButton("🔍 Жумуш издөө", callback_data="search"),
        telebot.types.InlineKeyboardButton("📝 Вакансия кошуу", callback_data="add"),
        telebot.types.InlineKeyboardButton("🗑 Менин вакансиям", callback_data="my"),
        telebot.types.InlineKeyboardButton("📢 Канал", url=CHANNEL_URL),
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
    return f"💼 <b>{v['title']}</b>\n\n🏙 Шаар: {v['city']}\n📂 Категория: {v['category']}\n💰 Айлык: <b>{v['salary']} сом</b>\n📝 {v['desc']}\n📞 Байланыш: <code>{v['phone']}</code>"

def send_home(chat_id):
    users.pop(chat_id, None)
    bot.send_message(chat_id, "🏠 <b>Башкы меню</b>\n\nТанда 👇", reply_markup=main_inline(), parse_mode="HTML")

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    users.pop(chat_id, None)
    d = load_data()
    all_users = d.get("users", [])
    if chat_id not in [u["id"] for u in all_users]:
        all_users.append({"id": chat_id, "name": message.from_user.first_name, "username": message.from_user.username})
        d["users"] = all_users
        save_data(d)
    # Астындагы кнопкаларды орнотобуз - эски категориялар өчөт
    bot.send_message(chat_id, "👋 <b>Салам! Мен - Жумуш Ботумун.</b>\n\n🇰🇬 Кыргызстан боюнча эң оңой жумуш издөө!", reply_markup=bottom_kb(), parse_mode="HTML")
    bot.send_message(chat_id, "Төмөндөн танда 👇", reply_markup=main_inline())

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, "ℹ️ <b>КАНТИП КОЛДОНСОҢ?</b>\n\n🔍 <b>Жумуш издөө:</b> Астындагы кнопканы бас → Шаар → Категория → Даяр!\n\n📝 <b>Вакансия кошуу:</b> Астындагы кнопканы бас → Шаар → Категория → Аты → Айлык → Телефон → Сүрөттөмө. Болду! Каналга да, ботко да чыгат.\n\n📢 <b>Канал:</b> Астындагы 📢 Каналды бассаң — дароо каналга өтөсүң.\n\n🔄 <b>Старт:</b> Эгер бир нерсе тыгылып калса — 🔄 Стартты бас, баары тазаланып калат.", reply_markup=bottom_kb(), parse_mode="HTML")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.chat.id != ADMIN_ID:
        return
    d = load_data()
    all_users = d.get("users", [])
    vacancies = d.get("vacancies", [])
    text = f"📊 <b>СТАТИСТИКА</b>\n\n👥 Адам: {len(all_users)}\n📝 Вакансия: {len(vacancies)}\n\n🆕 Акыркы адамдар:\n"
    for u in all_users[-10:]:
        text += f"- {u.get('name')} @{u.get('username')}\n"
    text += "\n💼 Акыркы вакансиялар:\n"
    for v in vacancies[-5:]:
        text += f"- {v['title']} | {v['city']} | {v['salary']}\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=bottom_kb())

# --- АСТЫНДАГЫ КНОПКАЛАРДЫ БАСКАНДА ---
@bot.message_handler(func=lambda m: m.text in ["🔍 Жумуш издөө", "📝 Вакансия кошуу", "📢 Канал", "ℹ️ Жардам", "🔄 Старт", "🔙 Артка"])
def bottom_buttons(message):
    chat_id = message.chat.id
    txt = message.text
    if txt == "🔄 Старт" or txt == "🔙 Артка":
        start(message)
        return
    if txt == "📢 Канал":
        m = telebot.types.InlineKeyboardMarkup()
        m.add(telebot.types.InlineKeyboardButton("📢 Каналга өтүү", url=CHANNEL_URL))
        bot.send_message(chat_id, "📢 <b>Каналыбыз:</b>\n\nКүн сайын жаңы вакансиялар 👇", reply_markup=m, parse_mode="HTML")
        return
    if txt == "ℹ️ Жардам":
        help_cmd(message)
        return
    if txt == "🔍 Жумуш издөө":
        users[chat_id] = {"step": "search_city"}
        bot.send_message(chat_id, "📍 <b>Кайсы шаардан издейсиң?</b>", reply_markup=cities_kb("search"), parse_mode="HTML")
        return
    if txt == "📝 Вакансия кошуу":
        users[chat_id] = {"step": "add_city"}
        bot.send_message(chat_id, "📍 <b>Вакансия кайсы шаарда?</b>", reply_markup=cities_kb("add"), parse_mode="HTML")
        return

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)
    if data == "home":
        send_home(chat_id)
        return
    if data == "help":
        bot.edit_message_text("ℹ️ <b>КАНТИП КОЛДОНСОҢ?</b>\n\n🔍 <b>Жумуш издөө:</b> Астындагы кнопка → Шаар → Категория\n\n📝 <b>Вакансия кошуу:</b> Астындагы кнопка → Шаар → Категория → Аты → Айлык → Телефон → Сүрөттөмө\n\n📢 <b>Канал:</b> Астындагы 📢 Каналды бас — дароо өтөсүң.\n\n🔄 Эгер тыгылып калса — астындагы 🔄 Стартты бас.", chat_id, call.message.message_id, reply_markup=main_inline(), parse_mode="HTML")
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
            bot.edit_message_text("😔 Сенин азырынча вакансияң жок.", chat_id, call.message.message_id, reply_markup=main_inline())
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
            d = load_data()
            vacancies = d.get("vacancies", [])
            deleted = vacancies.pop(idx)
            d["vacancies"] = vacancies
            save_data(d)
            bot.edit_message_text(f"✅ Өчүрүлдү: {deleted['title']}", chat_id, call.message.message_id, reply_markup=main_inline())
        except:
            bot.edit_message_text("Ката кетти.", chat_id, call.message.message_id, reply_markup=main_inline())
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
        users.pop(chat_id, None)
        if not found:
            bot.edit_message_text(f"😔 {city} - {cat} боюнча азырынча вакансия жок.\n\nАстындагы 🔄 Стартты басып, кайра аракет кыл.", chat_id, call.message.message_id, reply_markup=main_inline())
            return
        bot.edit_message_text(f"✅ {city} - {cat} боюнча {len(found)} вакансия табылды 👇", chat_id, call.message.message_id, reply_markup=main_inline())
        for v in found:
            bot.send_message(chat_id, vacancy_card(v), parse_mode="HTML", reply_markup=bottom_kb())
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
        bot.send_message(chat_id, "✏️ <b>Вакансиянын атын жаз:</b>\nМисалы: Курьер керек", parse_mode="HTML", reply_markup=bottom_kb())
        return

@bot.message_handler(func=lambda m: True)
def texts(message):
    chat_id = message.chat.id
    st = users.get(chat_id)
    if not st:
        bot.send_message(chat_id, "Астындагы кнопкадан танда 👇", reply_markup=bottom_kb())
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
        d = load_data()
        vacancies = d.get("vacancies", [])
        new_v = {"user_id": chat_id, "city": st["city"], "category": st["category"], "title": st["title"], "salary": st["salary"], "phone": st["phone"], "desc": txt}
        vacancies.append(new_v)
        d["vacancies"] = vacancies
        save_data(d)
        users.pop(chat_id, None)
        bot.send_message(chat_id, "✅ <b>Вакансия сакталды!</b>\n\nЭми ал боттон да, каналдан да көрүнөт. Өчпөйт!", reply_markup=bottom_kb(), parse_mode="HTML")
        bot.send_message(chat_id, "Танда 👇", reply_markup=main_inline())
        try:
            bot.send_message(ADMIN_ID, f"🆕 ЖАҢЫ ВАКАНСИЯ\n\n💼 {new_v['title']}\n🏙 {new_v['city']} | {new_v['category']}\n💰 {new_v['salary']}\n📞 {new_v['phone']}\n📝 {new_v['desc']}")
        except:
            pass
        try:
            channel_text = f"💼 <b>ЖАҢЫ ВАКАНСИЯ!</b>\n\n💼 {new_v['title']}\n🏙 Шаар: {new_v['city']}\n📂 Категория: {new_v['category']}\n💰 Айлык: <b>{new_v['salary']} сом</b>\n📞 Байланыш: <code>{new_v['phone']}</code>\n📝 {new_v['desc']}\n\n👇 Бардык вакансиялар:\n@bishkek_jobs_kg_bot"
            bot.send_message(CHANNEL_ID, channel_text, parse_mode="HTML")
        except Exception as e:
            print(f"Каналга чыгарууда ката: {e}")
        return

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot ishтеп жатат! V7"

def run_bot():
    print("Бот иштеп жатат... V7")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
