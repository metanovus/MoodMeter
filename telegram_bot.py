import os
import hashlib

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

import mood_calculator
import transformers_mood
from lib.postgresql_manager import PostgreSQLConnector

load_dotenv()

# Переменные окружения для подключения тг чата и админа по id
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')

conn = PostgreSQLConnector()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def save_message_to_sql(chat_id, user_id, message_text, message_label, label_score, chat_mood, message_datetime,
                        table_name='message_analysis'):
    data = [(chat_id, user_id, message_text, message_datetime, message_label, label_score, chat_mood)]
    columns = ['chat_id', 'user_id', 'message_text', 'message_datetime', 'message_label', 'label_score', 'chat_mood']
    conn.insert_data(data, table_name, columns)


def save_user_to_sql(user_id, password, table_name='user_credentials'):
    data = [(user_id, password)]
    columns = ['user_id', 'password']
    conn.insert_data(data, table_name, columns)


def save_chat_to_sql(user_id, chat_id, table_name='user_chat'):
    data = [(user_id, chat_id)]
    columns = ['user_id', 'chat_id']
    conn.insert_data(data, table_name, columns)


def handle_message(update: Update, context: CallbackContext):
    """
    Processes incoming messages, analyzes sentiment, and handles negative sentiment alerts.

    Args:
        update (Update): The incoming update from the Telegram chat.
        context (CallbackContext): The context passed by the Telegram bot, used to manage bot interaction and state.

    Returns:
        None
    """

    message_datetime = update.message.date
    chat_id = update.message.chat_id
    user = update.message.from_user
    message_text = update.message.text
    print(f'Message from channel: {chat_id}')

    message_label, label_score = transformers_mood.predict_sentiment(message_text)

    chat_mood = mood_calculator.calculate_weighted_sentiment(message_label, label_score)

    save_message_to_sql(chat_id=chat_id,
                        user_id=user.id,
                        message_text=message_text,
                        message_datetime=message_datetime,
                        message_label=message_label,
                        label_score=label_score,
                        chat_mood=chat_mood)

    # Проверка на негативное сообщение с высоким label_score
    if message_label == "NEGATIVE" and label_score > 0.65:
        # Отправка сообщения администратору
        alert_message = (f"Внимание! В чате обнаружено негативное сообщение:\n\n"
                         f"Пользователь: (@{user.username})\n"
                         f"Сообщение: {message_text}\n"
                         f"Оценка негативности: {label_score:.2f}")

        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_message)

    print(f"User: {user.first_name} {user.last_name} (@{user.username})")
    print(f"Message: {message_text}")
    print(message_label, label_score, 'MOOD:', chat_mood)


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Используйте команду /add_user, чтобы добавить свой user_id.')
    update.message.reply_text('Или команду /add_chat chat_id, чтобы добавить chat_id в базу данных')


def add_user(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != 'private':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Эта команда доступна только в личных сообщениях.')
        return

    user_id = update.message.from_user.id
    password = hash_password(str(user_id))
    query_user = f"""select user_id 
                    from public.user_credentials 
                    where user_id={user_id}"""
    users = conn.read_data_to_dataframe(query_user)
    if len(users) == 0:
        save_user_to_sql(user_id, password)
        update.message.reply_text(f"Ваш user_id: {user_id} был записан")
        return
    update.message.reply_text(f"Такой user_id: {user_id} уже есть в базе")


def add_chat_command(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != 'private':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Эта команда доступна только в личных сообщениях.')
        return

    if len(context.args) != 1:
        update.message.reply_text('Пожалуйста, укажите ID чата, который нужно добавить.')
        return

    try:
        user_id = update.message.from_user.id
        chat_id = int(context.args[0])
    except ValueError:
        update.message.reply_text('ID чата должен быть числом.')
        return

    save_chat_to_sql(user_id, chat_id)
    update.message.reply_text(f'Чат с ID {chat_id} добавлен в базу данных.')


def deactivate_chat(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != 'private':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Эта команда доступна только в личных сообщениях.')
        return

    if len(context.args) != 1:
        update.message.reply_text('Пожалуйста, укажите ID чата, который нужно убрать.')
        return

    try:
        user_id = update.message.from_user.id
        chat_id = int(context.args[0])
    except ValueError:
        update.message.reply_text('ID чата должен быть числом.')
        return

    query_admin = f"""SELECT user_id 
                      FROM public.user_chat
                      WHERE chat_id = {chat_id}"""

    admin_data = conn.read_data_to_dataframe(query_admin)

    if admin_data.empty or admin_data.iloc[0].user_id != user_id:
        update.message.reply_text('Вы не админ этого чата')
        return

    # Удаляем чат из базы данных (функция, которую нужно реализовать)
    # deactivate_chat_from_sql(user_id, chat_id)

    update.message.reply_text(f'Чат с ID {chat_id} убран из активных.')


# Стоит точно перепроверить эту функцию в будущем
def welcome(update: Update, context: CallbackContext) -> None:
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat_id = update.effective_chat.id
            read_chat_history(context.bot, chat_id, 50)
            break


def read_chat_history(bot, chat_id, count):
    messages = bot.get_chat_history(chat_id, limit=count)

    for message in messages:
        if message.text:
            handle_message(message, bot)


def main():
    """
    Initializes the Telegram bot, sets up message handling, and starts polling for updates.

    Args:
        None

    Returns:
        None
    """

    updater = Updater(token=TOKEN, use_context=True)
    bot = updater.bot
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('add_user', add_user))
    dispatcher.add_handler(CommandHandler('add_chat', add_chat_command))
    dispatcher.add_handler(CommandHandler('deactivate_chat', deactivate_chat))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
