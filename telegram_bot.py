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


def save_user_to_sql(id, user_id, password, table_name='user_credentials'):
    data = [(id, user_id, password)]
    columns = ['id', 'user_id', 'password']
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

    # deprecated. need to be removed
    mood_calculator.save_message(chat_id, message_label, label_score, chat_mood, message_datetime)

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
    update.message.reply_text('Или команду /add_chat, чтобы добавить чат в базу данных')

def add_user(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != 'private':
        context.bot.send_message(chat_id=update.effective_chat.id, text='Эта команда доступна только в личных сообщениях.')
        return
    user_id = update.message.from_user.id
    password = hash_password(str(user_id))
    save_user_to_sql(2, user_id, password)
    update.message.reply_text(f"Ваш user_id: {user_id} был записан")

def add_chat(user_id: int, chat_id: int):
    save_chat_to_sql(user_id, chat_id)
    

def add_chat_command(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != 'private':
        context.bot.send_message(chat_id=update.effective_chat.id, text='Эта команда доступна только в личных сообщениях.')
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
    
    add_chat(user_id, chat_id)
    update.message.reply_text(f'Чат с ID {chat_id} добавлен в базу данных.')

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
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('add_user', add_user))
    dispatcher.add_handler(CommandHandler('add_chat', add_chat_command))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
