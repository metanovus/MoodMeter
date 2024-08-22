import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

import mood_calculator
import transformers_mood
from lib.postgresql_manager import PostgreSQLConnector

load_dotenv()

# Переменные окружения для подключения тг чата и админа по id
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')

conn = PostgreSQLConnector()


def save_message_to_sql(chat_id, user_id, message_text, message_label, label_score, chat_mood, message_datetime,
                        table_name='message_analysis'):
    data = [(chat_id, user_id, message_text, message_datetime, message_label, label_score, chat_mood)]
    columns = ['chat_id', 'user_id', 'message_text', 'message_datetime', 'message_label', 'label_score', 'chat_mood']
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
    print(f'Message from channel: {message_text}')

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

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
