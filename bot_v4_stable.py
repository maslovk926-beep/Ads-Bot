import telebot
from telebot import types
import sqlite3
import datetime
import time

from config import TOKEN, OWNER_ID, CHANNEL_ID


bot = telebot.TeleBot(TOKEN)


DB = "ads.db"


# =====================
# БАЗА ДАННЫХ
# =====================

def connect():
    return sqlite3.connect(DB)



def init_database():

    con = connect()
    cur = con.cursor()


    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT DEFAULT 'user',
        agreed INTEGER DEFAULT 0,
        created TEXT
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS ads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        title TEXT,
        description TEXT,
        price TEXT,
        city TEXT,
        contact TEXT,
        photo TEXT,
        status TEXT DEFAULT 'moderation',
        moderator TEXT,
        reason TEXT,
        created TEXT
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        created TEXT
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorites(
        user_id INTEGER,
        ad_id INTEGER
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ad_id INTEGER,
        reason TEXT,
        created TEXT
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)


    con.commit()
    con.close()



init_database()



# =====================
# НАСТРОЙКИ
# =====================


CATEGORIES = [
    "🚗 Авто",
    "🏠 Недвижимость",
    "📦 Товары",
    "🛠 Услуги",
    "💼 Работа",
    "🔹 Другое"
]


RULES = """
⚠️ Правила сервиса

Вы используете рекламный бот.

Администрация сервиса не является участником сделок.

Пользователь самостоятельно отвечает за:
• содержание объявления;
• предоставленные контакты;
• общение с другими пользователями;
• безопасность сделки.

Раскрытие личных данных происходит
на ответственность пользователя.

Продолжая использование бота,
вы соглашаетесь с правилами.
"""



user_cache = {}



# =====================
# РАБОТА С ПОЛЬЗОВАТЕЛЯМИ
# =====================


def save_user(user):

    con = connect()
    cur = con.cursor()


    cur.execute("""
    INSERT OR IGNORE INTO users
    (id, username, created)
    VALUES(?,?,?)
    """,
    (
        user.id,
        user.username,
        str(datetime.datetime.now())
    ))


    if user.id == OWNER_ID:

        cur.execute("""
        UPDATE users
        SET role='owner'
        WHERE id=?
        """,
        (OWNER_ID,))


    con.commit()
    con.close()



def get_role(user_id):

    con = connect()
    cur = con.cursor()


    cur.execute(
        "SELECT role FROM users WHERE id=?",
        (user_id,)
    )


    result = cur.fetchone()

    con.close()


    if result:
        return result[0]

    return "user"



def is_moderator(user_id):

    return get_role(user_id) in [
        "owner",
        "admin"
    ]



def get_name(user):

    if user.username:

        return "@" + user.username

    return user.first_name



def write_log(user, action):

    con = connect()
    cur = con.cursor()


    cur.execute("""
    INSERT INTO logs
    (user, action, created)
    VALUES(?,?,?)
    """,
    (
        user,
        action,
        str(datetime.datetime.now())
    ))


    con.commit()
    con.close()



print("v4 ядро загружено")# =====================
# АДМИН-ПАНЕЛЬ
# =====================


@bot.message_handler(commands=["admin"])
def admin_panel(message):

    if get_role(message.chat.id) != "owner":

        bot.send_message(
            message.chat.id,
            "❌ Доступ только владельцу"
        )

        return


    kb = types.InlineKeyboardMarkup()


    kb.add(
        types.InlineKeyboardButton(
            "👥 Менеджеры",
            callback_data="manager_menu"
        )
    )


    kb.add(
        types.InlineKeyboardButton(
            "📊 Статистика",
            callback_data="stats"
        )
    )


    kb.add(
        types.InlineKeyboardButton(
            "📜 Логи",
            callback_data="logs"
        )
    )


    kb.add(
        types.InlineKeyboardButton(
            "⚙️ Настройки",
            callback_data="settings"
        )
    )


    bot.send_message(
        message.chat.id,
        "👑 Админ-панель",
        reply_markup=kb
    )



# =====================
# ДОБАВИТЬ МЕНЕДЖЕРА
# =====================


@bot.message_handler(commands=["add_admin"])
def add_admin(message):

    if message.chat.id != OWNER_ID:
        return


    try:

        user_id = int(
            message.text.split()[1]
        )


        con = connect()
        cur = con.cursor()


        cur.execute("""
        INSERT OR IGNORE INTO users
        (id, role, created)
        VALUES(?,?,?)
        """,
        (
            user_id,
            "admin",
            str(datetime.datetime.now())
        ))


        cur.execute("""
        UPDATE users
        SET role='admin'
        WHERE id=?
        """,
        (user_id,))


        con.commit()
        con.close()


        write_log(
            str(message.chat.id),
            f"Добавил менеджера {user_id}"
        )


        bot.reply_to(
            message,
            "✅ Менеджер добавлен"
        )


    except:

        bot.reply_to(
            message,
            "Использование:\n/add_admin ID"
        )



# =====================
# УДАЛИТЬ МЕНЕДЖЕРА
# =====================


@bot.message_handler(commands=["remove_admin"])
def remove_admin(message):

    if message.chat.id != OWNER_ID:
        return


    try:

        user_id = int(
            message.text.split()[1]
        )


        con = connect()
        cur = con.cursor()


        cur.execute("""
        UPDATE users
        SET role='user'
        WHERE id=?
        """,
        (user_id,))


        con.commit()
        con.close()


        write_log(
            str(message.chat.id),
            f"Удалил менеджера {user_id}"
        )


        bot.reply_to(
            message,
            "❌ Права менеджера сняты"
        )


    except:

        bot.reply_to(
            message,
            "Использование:\n/remove_admin ID"
        )



# =====================
# СПИСОК МЕНЕДЖЕРОВ
# =====================


@bot.message_handler(commands=["admins"])
def admins(message):

    if message.chat.id != OWNER_ID:
        return


    con = connect()
    cur = con.cursor()


    cur.execute("""
    SELECT id, username
    FROM users
    WHERE role='admin'
    """)


    admins = cur.fetchall()

    con.close()



    text = "🛡 Менеджеры:\n\n"


    if not admins:

        text += "Нет менеджеров"

    else:

        for admin in admins:

            username = admin[1]

            if username:

                text += (
                    f"@{username} "
                    f"({admin[0]})\n"
                )

            else:

                text += (
                    f"ID: {admin[0]}\n"
                )



    bot.send_message(
        message.chat.id,
        text
    )



# =====================
# МЕНЮ МЕНЕДЖЕРОВ
# =====================


@bot.callback_query_handler(
    func=lambda c: c.data=="manager_menu"
)
def manager_menu(call):

    if call.from_user.id != OWNER_ID:
        return


    bot.send_message(
        call.message.chat.id,
        """
👥 Управление менеджерами

Добавить:
 /add_admin ID

Удалить:
 /remove_admin ID

Список:
 /admins
"""
    )# =====================
# START
# =====================


@bot.message_handler(commands=["start"])
def start(message):

    save_user(message.from_user)


    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )


    kb.add(
        "📢 Создать объявление",
        "📦 Мои объявления"
    )


    kb.add(
        "📜 Правила",
        "👤 Профиль"
    )


    bot.send_message(
        message.chat.id,
        "Добро пожаловать в сервис объявлений.\n\n"
        + RULES,
        reply_markup=kb
    )



# =====================
# СОЗДАНИЕ ОБЪЯВЛЕНИЯ
# =====================


@bot.message_handler(
    func=lambda m: m.text=="📢 Создать объявление"
)
def create_ad(message):

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )


    for category in CATEGORIES:

        kb.add(category)


    kb.add("❌ Отмена")


    bot.send_message(
        message.chat.id,
        "Выберите категорию:",
        reply_markup=kb
    )


    bot.register_next_step_handler(
        message,
        category_step
    )



def category_step(message):

    if message.text=="❌ Отмена":

        cancel(message)
        return


    user_cache[message.chat.id] = {

        "category": message.text

    }


    bot.send_message(
        message.chat.id,
        "Введите название объявления:"
    )


    bot.register_next_step_handler(
        message,
        title_step
    )



def title_step(message):

    user_cache[message.chat.id]["title"] = message.text


    bot.send_message(
        message.chat.id,
        "Введите описание товара или услуги:"
    )


    bot.register_next_step_handler(
        message,
        description_step
    )



def description_step(message):

    user_cache[message.chat.id]["description"] = message.text


    bot.send_message(
        message.chat.id,
        "Введите цену:"
    )


    bot.register_next_step_handler(
        message,
        price_step
    )



def price_step(message):

    user_cache[message.chat.id]["price"] = message.text


    bot.send_message(
        message.chat.id,
        "Введите город:"
    )


    bot.register_next_step_handler(
        message,
        city_step
    )



def city_step(message):

    user_cache[message.chat.id]["city"] = message.text


    bot.send_message(
        message.chat.id,
        "Введите контакт для связи:"
    )


    bot.register_next_step_handler(
        message,
        contact_step
    )



def contact_step(message):

    user_cache[message.chat.id]["contact"] = message.text


    bot.send_message(
        message.chat.id,
        "Отправьте фото объявления или напишите: нет"
    )


    bot.register_next_step_handler(
        message,
        photo_step
    )



def photo_step(message):

    data = user_cache[message.chat.id]


    photo = None


    if message.content_type == "photo":

        photo = message.photo[-1].file_id


    data["photo"] = photo



    con = connect()
    cur = con.cursor()


    cur.execute("""
    INSERT INTO ads
    (
    user_id,
    category,
    title,
    description,
    price,
    city,
    contact,
    photo,
    created
    )
    VALUES(?,?,?,?,?,?,?,?,?)
    """,
    (
        message.chat.id,
        data["category"],
        data["title"],
        data["description"],
        data["price"],
        data["city"],
        data["contact"],
        data["photo"],
        str(datetime.datetime.now())
    ))


    ad_id = cur.lastrowid


    con.commit()
    con.close()



    text = f"""
🆕 Новое объявление #{ad_id}

📂 Категория:
{data['category']}

📌 Название:
{data['title']}

📝 Описание:
{data['description']}

💰 Цена:
{data['price']}

📍 Город:
{data['city']}

📞 Контакт:
{data['contact']}
"""



    keyboard = types.InlineKeyboardMarkup()


    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Одобрить",
            callback_data=f"approve_{ad_id}"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=f"decline_{ad_id}"
        )
    )



    # отправляем владельцу

    bot.send_message(
        OWNER_ID,
        text,
        reply_markup=keyboard
    )



    # отправляем менеджерам

    con = connect()
    cur = con.cursor()


    cur.execute("""
    SELECT id
    FROM users
    WHERE role='admin'
    """)


    managers = cur.fetchall()

    con.close()



    for manager in managers:

        try:

            bot.send_message(
                manager[0],
                text,
                reply_markup=keyboard
            )

        except:

            pass



    bot.send_message(
        message.chat.id,
        "✅ Объявление отправлено на модерацию"
    )


    user_cache.pop(
        message.chat.id,
        None
    )



# =====================
# ОТМЕНА
# =====================


@bot.message_handler(
    func=lambda m: m.text=="❌ Отмена"
)
def cancel(message):

    user_cache.pop(
        message.chat.id,
        None
    )


    bot.send_message(
        message.chat.id,
        "❌ Создание объявления отменено"
    )# =====================
# ОДОБРЕНИЕ ОБЪЯВЛЕНИЯ
# =====================


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("approve_")
)
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


    con = connect()
    cur = con.cursor()


    cur.execute(
        "SELECT * FROM ads WHERE id=?",
        (ad_id,)
    )


    ad = cur.fetchone()



    if not ad:

        con.close()

        bot.answer_callback_query(
            call.id,
            "Объявление не найдено"
        )

        return



    if ad[9] != "moderation":

        con.close()

        bot.answer_callback_query(
            call.id,
            "⚠️ Уже обработано"
        )

        return



    moderator = get_name(
        call.from_user
    )



    cur.execute("""
    UPDATE ads
    SET status='published',
        moderator=?
    WHERE id=?
    """,
    (
        moderator,
        ad_id
    ))


    con.commit()
    con.close()



    post = f"""
{ad[2]}

📂 {ad[3]}

📝 {ad[4]}

💰 Цена: {ad[5]}

📍 Город: {ad[6]}

📞 Контакт: {ad[7]}


────────────
✅ Одобрено модератором {moderator}
"""



    try:

        if ad[8]:

            bot.send_photo(
                CHANNEL_ID,
                ad[8],
                caption=post
            )

        else:

            bot.send_message(
                CHANNEL_ID,
                post
            )


    except Exception as e:

        bot.send_message(
            call.message.chat.id,
            "❌ Ошибка публикации в канал"
        )

        return



    write_log(
        moderator,
        f"Одобрил объявление #{ad_id}"
    )



    try:

        bot.send_message(
            ad[1],
            f"""
✅ Ваше объявление опубликовано!

Номер:
#{ad_id}
"""
        )

    except:

        pass



    bot.answer_callback_query(
        call.id,
        "✅ Опубликовано"
    )



# =====================
# ОТКЛОНЕНИЕ
# =====================


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("decline_")
)
def decline_ad(call):

    if not is_moderator(call.from_user.id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет прав"
        )

        return



    ad_id = int(
        call.data.split("_")[1]
    )


    user_cache[call.from_user.id] = {
        "decline_id": ad_id
    }



    bot.send_message(
        call.from_user.id,
        "Введите причину отклонения:"
    )


    bot.register_next_step_handler(
        call.message,
        save_decline
    )



def save_decline(message):

    data = user_cache.get(
        message.chat.id
    )


    if not data:

        return



    ad_id = data["decline_id"]



    con = connect()
    cur = con.cursor()



    cur.execute(
        "SELECT user_id FROM ads WHERE id=?",
        (ad_id,)
    )


    owner = cur.fetchone()



    cur.execute("""
    UPDATE ads
    SET status='rejected',
        reason=?,
        moderator=?
    WHERE id=?
    """,
    (
        message.text,
        get_name(message.from_user),
        ad_id
    ))



    con.commit()
    con.close()



    write_log(
        get_name(message.from_user),
        f"Отклонил объявление #{ad_id}"
    )



    if owner:

        try:

            bot.send_message(
                owner[0],
                f"""
❌ Ваше объявление #{ad_id} отклонено.

Причина:
{message.text}
"""
            )

        except:

            pass



    bot.send_message(
        message.chat.id,
        "❌ Объявление отклонено"
    )



    user_cache.pop(
        message.chat.id,
        None
    )



# =====================
# МОИ ОБЪЯВЛЕНИЯ
# =====================


@bot.message_handler(
    func=lambda m: m.text=="📦 Мои объявления"
)
def my_ads(message):

    con = connect()
    cur = con.cursor()


    cur.execute("""
    SELECT id,title,status
    FROM ads
    WHERE user_id=?
    """,
    (
        message.chat.id,
    ))


    ads = cur.fetchall()

    con.close()



    if not ads:

        bot.send_message(
            message.chat.id,
            "У вас нет объявлений"
        )

        return



    text = "📦 Ваши объявления:\n\n"



    for ad in ads:

        status = {
            "moderation":"🟡 Проверка",
            "published":"🟢 Опубликовано",
            "rejected":"🔴 Отклонено"
        }.get(
            ad[2],
            ad[2]
        )


        text += (
            f"#{ad[0]} {ad[1]}\n"
            f"{status}\n\n"
        )



    bot.send_message(
        message.chat.id,
        text
    )# =====================
# СТАТИСТИКА
# =====================


@bot.callback_query_handler(
    func=lambda c: c.data=="stats"
)
def statistics(call):

    if call.from_user.id != OWNER_ID:
        return


    con = connect()
    cur = con.cursor()


    cur.execute(
        "SELECT COUNT(*) FROM users"
    )
    users = cur.fetchone()[0]


    cur.execute(
        "SELECT COUNT(*) FROM ads"
    )
    ads = cur.fetchone()[0]


    cur.execute("""
    SELECT COUNT(*)
    FROM ads
    WHERE status='published'
    """)
    published = cur.fetchone()[0]


    cur.execute("""
    SELECT COUNT(*)
    FROM ads
    WHERE status='rejected'
    """)
    rejected = cur.fetchone()[0]


    cur.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE role='admin'
    """)
    admins = cur.fetchone()[0]


    con.close()


    bot.send_message(
        call.message.chat.id,
        f"""
📊 Статистика

👥 Пользователей:
{users}

📦 Объявлений:
{ads}

🟢 Опубликовано:
{published}

🔴 Отклонено:
{rejected}

🛡 Менеджеров:
{admins}
"""
    )



# =====================
# ЛОГИ
# =====================


@bot.callback_query_handler(
    func=lambda c: c.data=="logs"
)
def logs(call):

    if call.from_user.id != OWNER_ID:
        return


    con = connect()
    cur = con.cursor()


    cur.execute("""
    SELECT user,action,created
    FROM logs
    ORDER BY id DESC
    LIMIT 15
    """)


    result = cur.fetchall()

    con.close()



    text = "📜 Последние действия:\n\n"


    if not result:

        text += "Логов нет"

    else:

        for row in result:

            text += (
                f"👤 {row[0]}\n"
                f"⚙️ {row[1]}\n"
                f"🕒 {row[2]}\n\n"
            )



    bot.send_message(
        call.message.chat.id,
        text
    )



# =====================
# НАСТРОЙКИ
# =====================


@bot.callback_query_handler(
    func=lambda c: c.data=="settings"
)
def settings(call):

    if call.from_user.id != OWNER_ID:
        return


    bot.send_message(
        call.message.chat.id,
        """
⚙️ Настройки

Доступно:

👥 Управление менеджерами
📊 Статистика
📜 Логи

Дополнительные настройки
можно расширять дальше.
"""
    )



# =====================
# ПРАВИЛА
# =====================


@bot.message_handler(
    func=lambda m: m.text=="📜 Правила"
)
def rules(message):

    bot.send_message(
        message.chat.id,
        RULES
    )



# =====================
# ПРОФИЛЬ
# =====================


@bot.message_handler(
    func=lambda m: m.text=="👤 Профиль"
)
def profile(message):

    role = get_role(
        message.chat.id
    )


    bot.send_message(
        message.chat.id,
        f"""
👤 Профиль

ID:
{message.chat.id}

Роль:
{role}
"""
    )



# =====================
# ЖАЛОБЫ
# =====================


@bot.message_handler(commands=["report"])
def report(message):

    bot.send_message(
        message.chat.id,
        """
🚨 Отправьте:

номер объявления
+
причину жалобы
"""
    )


    bot.register_next_step_handler(
        message,
        save_report
    )



def save_report(message):

    text = message.text


    con = connect()
    cur = con.cursor()


    cur.execute("""
    INSERT INTO reports
    (user_id,reason,created)
    VALUES(?,?,?)
    """,
    (
        message.chat.id,
        text,
        str(datetime.datetime.now())
    ))


    con.commit()
    con.close()



    write_log(
        get_name(message.from_user),
        "Отправил жалобу"
    )


    bot.send_message(
        message.chat.id,
        "✅ Жалоба отправлена"
    )



# =====================
# ПОМОЩЬ
# =====================


@bot.message_handler(commands=["help"])
def help_command(message):

    bot.send_message(
        message.chat.id,
        """
🆘 Помощь

📢 Создать объявление
📦 Мои объявления
📜 Правила

Жалоба:
 /report

Админ:
 /admin
"""
    )



# =====================
# ЗАПУСК
# =====================


print("Ads-Bot v4 запущен")


while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:

        print(
            "Ошибка:",
            e
        )

        time.sleep(5)
