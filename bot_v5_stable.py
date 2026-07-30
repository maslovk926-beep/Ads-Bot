import telebot
from telebot import types
import datetime
import database
import config

TOKEN = config.TOKEN
OWNER_ID = config.OWNER_ID
CHANNEL_ID = config.CHANNEL_ID

bot = telebot.TeleBot(TOKEN)

database.init()

print("Ads-Bot v5 ядро загружено")


# =========================
# КЭШ СОСТОЯНИЙ
# =========================

user_cache = {}


# =========================
# ПРАВА
# =========================

def is_owner(user_id):
    return user_id == OWNER_ID


def is_manager(user_id):

    if is_owner(user_id):
        return True

    return database.get_role(user_id) == "manager"



def is_moderator(user_id):
    return is_manager(user_id)



# =========================
# КЛАВИАТУРЫ
# =========================

def main_menu():

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
        "📢 Подать объявление",
        "📦 Мои объявления"
    )

    kb.add(
        "🔍 Поиск",
        "❤️ Избранное"
    )

    kb.add(
        "👤 Профиль",
        "ℹ️ Помощь"
    )

    return kb



def owner_menu():

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
        "👥 Менеджеры",
        "📊 Статистика"
    )

    kb.add(
        "🚨 Жалобы",
        "📜 Логи"
    )

    kb.add(
        "📢 Рассылка",
        "💾 Бэкап"
    )

    kb.add(
        "⬅️ Назад"
    )

    return kb



# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    database.add_user(
        message.from_user.id,
        message.from_user.username or "unknown"
    )

    text = """
👋 Добро пожаловать в Ads-Bot v5

📢 Здесь можно размещать и искать объявления.

⚠️ Важно:
Вы самостоятельно передаёте контактные данные.
Владелец бота не отвечает за сделки между пользователями.

Используя бот, вы соглашаетесь с правилами.
"""

    if is_owner(message.from_user.id):

        bot.send_message(
            message.chat.id,
            text + "\n\n👑 Панель владельца доступна.",
            reply_markup=owner_menu()
        )

    else:

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_menu()
        )


# =========================
# OWNER PANEL
# =========================

@bot.message_handler(func=lambda m: m.text == "⚙️ Владелец")
def owner_panel(message):

    if not is_owner(message.from_user.id):
        return

    bot.send_message(
        message.chat.id,
        "👑 Панель владельца",
        reply_markup=owner_menu()
    )# =========================
# МЕНЕДЖЕРЫ
# =========================

@bot.message_handler(func=lambda m: m.text == "👥 Менеджеры")
def managers_menu(message):

    if not is_owner(message.from_user.id):
        return

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
        "➕ Добавить менеджера",
        "➖ Удалить менеджера"
    )

    kb.add(
        "📋 Список менеджеров"
    )

    kb.add(
        "⬅️ Назад"
    )

    bot.send_message(
        message.chat.id,
        "👥 Управление менеджерами",
        reply_markup=kb
    )


@bot.message_handler(func=lambda m: m.text == "📋 Список менеджеров")
def list_managers(message):

    if not is_owner(message.from_user.id):
        return

    managers = database.get_managers()

    if not managers:
        bot.send_message(
            message.chat.id,
            "Менеджеров пока нет."
        )
        return

    text = "👥 Менеджеры:\n\n"

    for user_id, username in managers:
        text += f"• @{username} | ID: {user_id}\n"

    bot.send_message(
        message.chat.id,
        text
    )


@bot.message_handler(func=lambda m: m.text == "➕ Добавить менеджера")
def add_manager_start(message):

    if not is_owner(message.from_user.id):
        return

    user_cache[message.chat.id] = {
        "action": "add_manager"
    }

    bot.send_message(
        message.chat.id,
        "Введите Telegram ID пользователя:"
    )


@bot.message_handler(func=lambda m: m.text == "➖ Удалить менеджера")
def remove_manager_start(message):

    if not is_owner(message.from_user.id):
        return

    user_cache[message.chat.id] = {
        "action": "remove_manager"
    }

    bot.send_message(
        message.chat.id,
        "Введите ID менеджера для удаления:"
    )



@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("action") == "add_manager")
def add_manager_finish(message):

    try:
        user_id = int(message.text)

        database.add_manager(
            user_id,
            str(user_id),
            message.from_user.id
        )

        bot.send_message(
            message.chat.id,
            "✅ Менеджер добавлен.",
            reply_markup=owner_menu()
        )

        user_cache.pop(
            message.chat.id,
            None
        )

    except:

        bot.send_message(
            message.chat.id,
            "❌ Неверный ID"
        )



@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("action") == "remove_manager")
def remove_manager_finish(message):

    try:

        user_id = int(message.text)

        database.remove_manager(
            user_id
        )

        bot.send_message(
            message.chat.id,
            "✅ Менеджер удалён.",
            reply_markup=owner_menu()
        )

        user_cache.pop(
            message.chat.id,
            None
        )

    except:

        bot.send_message(
            message.chat.id,
            "❌ Ошибка ID"
        )


# =========================
# СТАТИСТИКА
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):

    if not is_owner(message.from_user.id):
        return

    data = database.get_stats()

    text = f"""
📊 Статистика Ads-Bot v5

👤 Пользователи: {data['users']}
📢 Объявления: {data['ads']}
✅ Опубликовано: {data['published']}
"""

    bot.send_message(
        message.chat.id,
        text
    )# =========================
# СОЗДАНИЕ ОБЪЯВЛЕНИЯ
# =========================

@bot.message_handler(func=lambda m: m.text == "📢 Подать объявление")
def create_ad_start(message):

    if database.is_blacklisted(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "❌ Вы не можете создавать объявления."
        )
        return

    user_cache[message.chat.id] = {
        "step": "category",
        "data": {
            "user_id": message.from_user.id
        }
    }

    bot.send_message(
        message.chat.id,
        "Выберите категорию:"
    )


@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("step") == "category")
def category(message):

    user_cache[message.chat.id]["data"]["category"] = message.text
    user_cache[message.chat.id]["step"] = "title"

    bot.send_message(
        message.chat.id,
        "Введите название товара:"
    )


@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("step") == "title")
def title(message):

    user_cache[message.chat.id]["data"]["title"] = message.text
    user_cache[message.chat.id]["step"] = "description"

    bot.send_message(
        message.chat.id,
        "Введите описание:"
    )


@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("step") == "description")
def description(message):

    user_cache[message.chat.id]["data"]["description"] = message.text
    user_cache[message.chat.id]["step"] = "price"

    bot.send_message(
        message.chat.id,
        "Введите цену:"
    )


@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("step") == "price")
def price(message):

    user_cache[message.chat.id]["data"]["price"] = message.text
    user_cache[message.chat.id]["step"] = "city"

    bot.send_message(
        message.chat.id,
        "Введите город:"
    )


@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("step") == "city")
def city(message):

    user_cache[message.chat.id]["data"]["city"] = message.text
    user_cache[message.chat.id]["step"] = "contact"

    bot.send_message(
        message.chat.id,
        "Введите контакт:"
    )


@bot.message_handler(func=lambda m: user_cache.get(m.chat.id, {}).get("step") == "contact")
def contact(message):

    user_cache[message.chat.id]["data"]["contact"] = message.text
    user_cache[message.chat.id]["step"] = "photo"

    bot.send_message(
        message.chat.id,
        "Отправьте фото товара."
    )


@bot.message_handler(content_types=["photo"])
def photo(message):

    if message.chat.id not in user_cache:
        return

    if user_cache[message.chat.id].get("step") != "photo":
        return

    data = user_cache[message.chat.id]["data"]

    data["photo"] = message.photo[-1].file_id

    ad_id = database.add_ad(data)

    bot.send_message(
        message.chat.id,
        f"✅ Объявление #{ad_id} отправлено на модерацию.",
        reply_markup=main_menu()
    )

    # отправка модераторам
    for manager_id, username in database.get_managers():

        bot.send_message(
            manager_id,
            f"""
🆕 Новое объявление #{ad_id}

📌 {data['title']}
💰 {data['price']}
📍 {data['city']}
""",
        )

    user_cache.pop(
        message.chat.id,
        None
    )


# =========================
# МОДЕРАЦИЯ
# =========================

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def approve_ad(call):

    if not is_moderator(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "❌ Нет прав"
        )
        return

    ad_id = int(
        call.data.split("_")[1]
    )

    username = call.from_user.username or str(call.from_user.id)

    result = database.approve(
        ad_id,
        username
    )

    if result:

        database.log(
            username,
            "approve",
            ad_id
        )

        bot.answer_callback_query(
            call.id,
            "Одобрено"
        )

        bot.edit_message_text(
            "✅ Одобрено модератором @" + username,
            call.message.chat.id,
            call.message.message_id
        )

    else:

        bot.answer_callback_query(
            call.id,
            "Уже обработано"
        )


@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def reject_ad(call):

    if not is_moderator(call.from_user.id):
        return

    ad_id = int(
        call.data.split("_")[1]
    )

    username = call.from_user.username or str(call.from_user.id)

    database.reject(
        ad_id,
        username
    )

    database.log(
        username,
        "reject",
        ad_id
    )

    bot.answer_callback_query(
        call.id,
        "Отклонено"
    )# =========================
# ПОИСК
# =========================

@bot.message_handler(func=lambda m: m.text == "🔍 Поиск")
def search_start(message):

    user_cache[message.chat.id] = {
        "action": "search"
    }

    bot.send_message(
        message.chat.id,
        "Введите название, город или категорию:"
    )


@bot.message_handler(
    func=lambda m: user_cache.get(m.chat.id, {}).get("action") == "search"
)
def search(message):

    query = message.text.lower()

    con = database.connect()
    cur = con.cursor()

    cur.execute("""
    SELECT id,title,price,city
    FROM ads
    WHERE status='published'
    AND (
        lower(title) LIKE ?
        OR lower(city) LIKE ?
        OR lower(category) LIKE ?
    )
    """,
    (
        f"%{query}%",
        f"%{query}%",
        f"%{query}%"
    ))

    ads = cur.fetchall()

    con.close()

    if not ads:

        bot.send_message(
            message.chat.id,
            "Ничего не найдено.",
            reply_markup=main_menu()
        )

    else:

        text = "🔍 Найдено:\n\n"

        for ad in ads:
            text += (
                f"#{ad[0]} {ad[1]}\n"
                f"💰 {ad[2]}\n"
                f"📍 {ad[3]}\n\n"
            )

        bot.send_message(
            message.chat.id,
            text
        )

    user_cache.pop(
        message.chat.id,
        None
    )



# =========================
# ИЗБРАННОЕ
# =========================

@bot.message_handler(func=lambda m: m.text == "❤️ Избранное")
def favorites(message):

    ads = database.get_favorites(
        message.from_user.id
    )

    if not ads:

        bot.send_message(
            message.chat.id,
            "❤️ Избранных объявлений нет."
        )

        return


    text = "❤️ Избранное:\n\n"

    for ad in ads:
        text += f"Объявление #{ad[0]}\n"

    bot.send_message(
        message.chat.id,
        text
    )



# =========================
# ПРОФИЛЬ
# =========================

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):

    stats = database.get_stats()

    bot.send_message(
        message.chat.id,
        f"""
👤 Ваш профиль

🆔 ID:
{message.from_user.id}

⭐ Рейтинг:
новый пользователь

📢 Всего объявлений в системе:
{stats['ads']}
"""
    )



# =========================
# НАЗАД
# =========================

@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back(message):

    bot.send_message(
        message.chat.id,
        "Главное меню",
        reply_markup=main_menu()
    )



# =========================
# ЗАПУСК
# =========================

print("Ads-Bot v5 запущен")

bot.infinity_polling()
