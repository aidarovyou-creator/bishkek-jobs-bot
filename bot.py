import telebot, json, os
from flask import Flask
import threading

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8115276999

CITIES = ["Бишкек", "Ош", "Баткен", "Жалал-Абад", "Каракол", "Нарын", "Талас", "Чүй"]
CATEGORIES = ["🚴 Курьер", "☕ Официант", "🛒 Кассир", "🧹 Тазалоочу", "📞 Call-центр", "💻 IT / SMM", "📦 Башка"]

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

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Жумуш издөө", "📝 Вакансия кошуу")
    markup.add("🗑 Менин вакансиямды өчүрүү")
    return markup

def cities_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for c in CITIES:
        markup.add(c)
    markup.add("🔙 Артка")
    return markup

def categories_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for cat in CATEGORIES:
        markup.add(cat)
    markup.add("🔙 Артка")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            all_users = json.load(f)
    except:
        all_users = []
    if message.chat.id not in [u["id"] for u in all_users]:
        all_users.append({"id": message.chat.id, "name": message.from_user.first_name, "username": message.from_user.username})
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(all_users, f, ensure_ascii=False, indent=2)
    bot.send_message(message.chat.id, "👋 Салам! Мен - Жумуш Ботумун.\n\nКыргызстан боюнча жумуш издегендер үчүн!\n\nТөмөндөн танда:", reply_markup=main_menu())

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Бул команда тек админ үчүн.")
        return
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            all_users = json.load(f)
    except:
        all_users = []
    vacancies = load_vacancies()
    text = f"📊 СТАТИСТИКА\n\n👥 Бардык кирген адам: {len(all_users)}\n📝 Бардык вакансия: {len(vacancies)}\n\n🆕 Акыркы 10 адам:\n"
    for u in all_users[-10:]:
        text += f"- {u.get('name')} @{u.get('username')}\n"
    text += "\n💼 Акыркы вакансиялар:\n"
    for v in vacancies[-5:]:
        text += f"- {v['title']} | {v['city']} | {v['salary']}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🔙 Артка")
def back(message):
    users.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Башкы меню:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🔍 Жумуш издөө")
def search_start(message):
    users[message.chat.id] = {"step": "choose_city_search"}
    bot.send_message(message.chat.id, "Кайсы шаардан издейсиң?", reply_markup=cities_menu())

@bot.message_handler(func=lambda m: m.text == "📝 Вакансия кошуу")
def add_start(message):
    users[message.chat.id] = {"step": "choose_city_add"}
    bot.send_message(message.chat.id, "Вакансия кайсы шаарда?", reply_markup=cities_menu())

@bot.message_handler(func=lambda m: m.text == "🗑 Менин вакансиямды өчүрүү")
def delete_start(message):
    vacancies = load_vacancies()
    my = [(i, v) for i, v in enumerate(vacancies) if v["user_id"] == message.chat.id]
    if not my:
        bot.send_message(message.chat.id, "Сенин азырынча вакансияң жок.", reply_markup=main_menu())
        return
    users[message.chat.id] = {"step": "delete", "my": my}
    text = "Өчүргүң келгенди танда:\n\n"
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for idx, (i, v) in enumerate(my):
        text += f"{idx+1}. {v['title']} - {v['city']} - {v['salary']}\n"
        markup.add(f"Өчүр {idx+1}")
    markup.add("🔙 Артка")
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def all_messages(message):
    chat_id = message.chat.id
    text = message.text
    state = users.get(chat_id)
    if not state:
        bot.send_message(chat_id, "Менюдан танда:", reply_markup=main_menu())
        return
    step = state.get("step")
    if step == "choose_city_search":
        if text in CITIES:
            state["city"] = text
            state["step"] = "choose_cat_search"
            bot.send_message(chat_id, f"{text} шаары. Эми категорияны танда:", reply_markup=categories_menu())
        else:
            bot.send_message(chat_id, "Шаарды кнопкадан танда:", reply_markup=cities_menu())
        return
    if step == "choose_cat_search":
        if text in CATEGORIES:
            city = state["city"]
            vacancies = load_vacancies()
            found = [v for v in vacancies if v["city"] == city and v["category"] == text]
            if not found:
                bot.send_message(chat_id, f"😔 {city} - {text} боюнча азырынча вакансия жок.", reply_markup=main_menu())
            else:
                bot.send_message(chat_id, f"✅ {city} - {text} боюнча {len(found)} вакансия табылды:")
                for v in found:
                    bot.send_message(chat_id, f"💼 {v['title']}\n🏙 Шаар: {v['city']}\n📂 Категория: {v['category']}\n💰 Айлык: {v['salary']}\n📞 Байланыш: {v['phone']}\n📝 {v['desc']}")
                bot.send_message(chat_id, "Башкы меню:", reply_markup=main_menu())
            users.pop(chat_id, None)
        else:
            bot.send_message(chat_id, "Категорияны кнопкадан танда:", reply_markup=categories_menu())
        return
    if step == "choose_city_add":
        if text in CITIES:
            state["city"] = text
            state["step"] = "choose_cat_add"
            bot.send_message(chat_id, f"{text} шаары. Категорияны танда:", reply_markup=categories_menu())
        else:
            bot.send_message(chat_id, "Шаарды кнопкадан танда:", reply_markup=cities_menu())
        return
    if step == "choose_cat_add":
        if text in CATEGORIES:
            state["category"] = text
            state["step"] = "title"
            bot.send_message(chat_id, "Вакансиянын атын жаз:\nМисалы: Курьер керек", reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            bot.send_message(chat_id, "Категорияны кнопкадан танда:", reply_markup=categories_menu())
        return
    if step == "title":
        state["title"] = text
        state["step"] = "salary"
        bot.send_message(chat_id, "Айлыгы канча?\nМисалы: 45000")
        return
    if step == "salary":
        state["salary"] = text
        state["step"] = "phone"
        bot.send_message(chat_id, "Байланыш телефонуңду жаз:\nМисалы: 0700123456")
        return
    if step == "phone":
        state["phone"] = text
        state["step"] = "desc"
        bot.send_message(chat_id, "Вакансия жөнүндө кыскача жаз:")
        return
    if step == "desc":
        vacancies = load_vacancies()
        new_v = {"user_id": chat_id, "city": state["city"], "category": state["category"], "title": state["title"], "salary": state["salary"], "phone": state["phone"], "desc": text}
        vacancies.append(new_v)
        save_vacancies(vacancies)
        users.pop(chat_id, None)
        bot.send_message(chat_id, "✅ Вакансия кошулду! Рахмат!", reply_markup=main_menu())
        return
    if step == "delete":
        if text.startswith("Өчүр "):
            try:
                num = int(text.replace("Өчүр ", "")) - 1
                my = state["my"]
                real_index = my[num][0]
                vacancies = load_vacancies()
                deleted = vacancies.pop(real_index)
                save_vacancies(vacancies)
                users.pop(chat_id, None)
                bot.send_message(chat_id, f"🗑 Өчүрүлдү: {deleted['title']}", reply_markup=main_menu())
            except:
                bot.send_message(chat_id, "Ката кетти, кайра аракет кыл.")
        return

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot ishтеп жатат!"

def run_bot():
    print("Бот иштеп жатат... V4 - Server")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
