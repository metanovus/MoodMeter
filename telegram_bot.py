from telegram import Update, Bot
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import transformers_mood
import mood_calculator
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')


def handle_message(update: Update, context: CallbackContext):
    message_date = update.message.date
    chat_id = update.message.chat_id
    user = update.message.from_user
    message_text = update.message.text
    message_label, label_score = transformers_mood.predict_sentiment(message_text)

    chat_mood = mood_calculator.calculate_weighted_sentiment(message_label, label_score)
    mood_calculator.save_message(chat_id, message_label, label_score, chat_mood, message_date)

    print(f"User: {user.first_name} {user.last_name} (@{user.username})")
    print(f"Message: {message_text}")
    print(message_label, label_score, 'MOOD:', chat_mood)


def main():
    updater = Updater(token=TOKEN, use_context=True)
    bot = updater.bot

    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
