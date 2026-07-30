import telebot
from telebot import types

TOKEN = "8953313998:AAG2PirihextklZQeX7o5MC3V0_TZWNn6Wc"

ADMIN_CHAT_ID = 5213791057
CHANNEL_ID = -1003830895786

bot = telebot.TeleBot(TOKEN)

ads = {}


@bot.message_handler(commands=["start"])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    create = types.KeyboardButton("📢 Создать объявление")
    help_btn = types.KeyboardButton("ℹ️ Помощь")

    keyboard.add(create, help_btn)

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в сервис объявлений!",
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda m: m.text == "📢 Создать объявление")
def create_ad(message):
    bot.send_message(
        message.chat.id,
        "Отправьте одно сообщение:\n\n"
        "📷 Фото + описание\n"
        "или\n"
        "📝 Только текст"
    )

    bot.register_next_step_handler(message, get_ad)


def get_ad(message):

    keyboard = types.InlineKeyboardMarkup()

    publish = types.InlineKeyboardButton(
        "✅ Опубликовать",
        callback_data=f"publish_{message.chat.id}"
    )

    reject = types.InlineKeyboardButton(
        "❌ Отклонить",
        callback_data=f"reject_{message.chat.id}"
    )

    keyboard.add(publish, reject)


    if message.content_type == "photo":

        text = message.caption if message.caption else "Без описания"

        ads[message.chat.id] = {
            "type": "photo",
            "photo": message.photo[-1].file_id,
            "text": text
        }


        bot.send_photo(
            ADMIN_CHAT_ID,
            message.photo[-1].file_id,
            caption="Новое объявление:\n\n" + text,
            reply_markup=keyboard
        )


    else:

        ads[message.chat.id] = {
            "type": "text",
            "text": message.text
        }


        bot.send_message(
            ADMIN_CHAT_ID,
            "Новое объявление:\n\n" + message.text,
            reply_markup=keyboard
        )


    bot.send_message(
        message.chat.id,
        "Ваше объявление отправлено на модерацию."
    )



@bot.callback_query_handler(func=lambda call: call.data.startswith("publish_"))
def publish(call):

    user_id = int(call.data.split("_")[1])

    if user_id in ads:

        ad = ads[user_id]


        if ad["type"] == "photo":

            bot.send_photo(
                CHANNEL_ID,
                ad["photo"],
                caption=ad["text"]
            )

        else:

            bot.send_message(
                CHANNEL_ID,
                ad["text"]
            )


        bot.answer_callback_query(
            call.id,
            "Опубликовано!"
        )



@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject(call):

    user_id = int(call.data.split("_")[1])

    if user_id in ads:
        del ads[user_id]

    bot.answer_callback_query(
        call.id,
        "Отклонено"
    )



@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь")
def help(message):

    bot.send_message(
        message.chat.id,
        "Создайте объявление через кнопку 📢 Создать объявление."
    )



print("Бот запущен")

bot.infinity_polling()
