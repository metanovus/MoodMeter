import os
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

import mood_calculator
import transformers_mood
from lib.postgresql_manager import PostgreSQLConnector

conn = PostgreSQLConnector()

def save_message_to_sql(chat_id,
                        user_id,
                        message_text,
                        message_label,
                        label_score,
                        chat_mood,
                        message_datetime,
                        table_name='message_analysis'):
    data = [(chat_id, user_id, message_text, message_datetime, message_label, label_score, chat_mood)]
    columns = ['chat_id', 'user_id', 'message_text', 'message_datetime', 'message_label', 'label_score', 'chat_mood']
    conn.insert_data(data, table_name, columns)

def handle_message(update: Update, context: CallbackContext):
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

    if message_label == "NEGATIVE" and label_score > 0.65:
        alert_message = (f"Внимание! В чате обнаружено негативное сообщение:\n\n"
                         f"Пользователь: (@{user.username})\n"
                         f"Сообщение: {message_text}\n"
                         f"Оценка негативности: {label_score:.2f}")

        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_message)

    print(f"User: {user.first_name} {user.last_name} (@{user.username})")
    print(f"Message: {message_text}")
    print(message_label, label_score, 'MOOD:', chat_mood)

def main(token):
    updater = Updater(token=token, use_context=True)
    bot = updater.bot
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        token = sys.argv[1]
        main(token)
    else:
        print("Error: Telegram Bot TOKEN is required.")
