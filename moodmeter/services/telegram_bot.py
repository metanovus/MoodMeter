import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    Filters,
)
from telegram.error import TelegramError

from moodmeter.modules import transformers_mood, mood_calculator
from lib.postgresql_manager import PostgreSQLConnector
from moodmeter.utils.utils import hash_password, logger

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота и ID чата администратора из переменных окружения
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')

if not TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен в переменных окружения.")
    exit(1)

# Инициализация подключения к базе данных
conn = PostgreSQLConnector()


def save_message_to_sql(
        chat_id: int,
        user_id: int,
        message_text: str,
        message_label: str,
        label_score: float,
        chat_mood: float,
        message_datetime: datetime,
        table_name: str = 'message_analysis'
) -> None:
    """
    Сохраняет данные анализа сообщения в базу данных.

    Args:
        chat_id (int): ID чата.
        user_id (int): ID пользователя.
        message_text (str): Текст сообщения.
        message_label (str): Метка настроения сообщения.
        label_score (float): Уверенность в метке.
        chat_mood (float): Общий показатель настроения чата.
        message_datetime (datetime): Время отправки сообщения.
        table_name (str, optional): Название таблицы в БД. По умолчанию 'message_analysis'.
    """
    data = [
        (
            chat_id,
            user_id,
            message_text,
            message_datetime,
            message_label,
            label_score,
            chat_mood
        )
    ]
    columns = [
        'chat_id',
        'user_id',
        'message_text',
        'message_datetime',
        'message_label',
        'label_score',
        'chat_mood'
    ]
    try:
        conn.insert_data(data, table_name, columns)
    except Exception as e:
        logger.error(f"Ошибка при сохранении сообщения в SQL: {e}")


def save_user_to_sql(
        user_id: int,
        password: str,
        table_name: str = 'user_credentials'
) -> None:
    """
    Сохраняет данные пользователя в базу данных.

    Args:
        user_id (int): ID пользователя.
        password (str): Захешированный пароль.
        table_name (str, optional): Название таблицы в БД. По умолчанию 'user_credentials'.
    """
    data = [(user_id, password)]
    columns = ['user_id', 'password']
    try:
        conn.insert_data(data, table_name, columns)
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя в SQL: {e}")


def save_chat_to_sql(
        user_id: int,
        chat_id: int,
        table_name: str = 'user_chat'
) -> None:
    """
    Сохраняет связь пользователя с чатом в базу данных.

    Args:
        user_id (int): ID пользователя.
        chat_id (int): ID чата.
        table_name (str, optional): Название таблицы в БД. По умолчанию 'user_chat'.
    """
    data = [(user_id, chat_id)]
    columns = ['user_id', 'chat_id']
    try:
        conn.insert_data(data, table_name, columns)
    except Exception as e:
        logger.error(f"Ошибка при сохранении связи пользователя с чатом в SQL: {e}")


def deactivate_chat_in_sql(chat_id: int, table_name: str = 'chat') -> None:
    """
    Деактивирует чат в базе данных.

    Args:
        chat_id (int): ID чата.
        table_name (str, optional): Название таблицы в БД. По умолчанию 'chat'.
    """
    try:
        conn.update_data(table_name, 'chat_id', chat_id, 'status', 'deactivated')
    except Exception as e:
        logger.error(f"Ошибка при деактивации чата в SQL: {e}")


def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Обрабатывает входящие сообщения, анализирует настроение и отправляет оповещения.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    message = update.message
    if not message or not message.text:
        return  # Игнорируем не-текстовые сообщения

    message_datetime = message.date
    chat_id = message.chat_id
    user = message.from_user
    message_text = message.text

    try:
        # Проверка, активен ли чат в БД
        query_status_chat = "SELECT status FROM public.chat WHERE chat_id = %s"
        status_chat_data = conn.read_data(query_status_chat, (chat_id,))
        if not status_chat_data:
            # Если чат не найден в базе данных
            context.bot.send_message(
                chat_id=chat_id,
                text="Этот чат не настроен для мониторинга настроений. Пожалуйста, свяжитесь с администратором для получения дополнительной информации."
            )
            return

        status_chat = status_chat_data[0][0]
    except Exception as e:
        # Обработка ошибок при запросе к базе данных
        logger.error(f"Ошибка при проверке статуса чата: {e}")
        try:
            context.bot.send_message(
                chat_id=chat_id,
                text="Произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте позже."
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")
        return

    if status_chat == 'active':
        try:
            # Анализ настроения сообщения
            message_label, label_score = transformers_mood.predict_sentiment(message_text)

            # Вычисление общего настроения чата
            chat_mood = mood_calculator.calculate_weighted_sentiment(message_label, label_score)

            # Сохранение данных в базу
            save_message_to_sql(
                chat_id=chat_id,
                user_id=user.id,
                message_text=message_text,
                message_datetime=message_datetime,
                message_label=message_label,
                label_score=label_score,
                chat_mood=chat_mood
            )

            # Логирование сообщений (опционально можно убрать в продакшене)
            logger.info(f"User: {user.full_name} (@{user.username})")
            logger.info(f"Message: {message_text}")
            logger.info(f"Label: {message_label}, Score: {label_score}, Mood: {chat_mood}")
        except Exception as e:
            # Обработка ошибок при анализе настроений и сохранении данных
            logger.error(f"Ошибка при обработке сообщения: {e}")
            try:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="Произошла ошибка при анализе вашего сообщения. Пожалуйста, попробуйте позже."
                )
            except TelegramError as te:
                logger.error(f"Ошибка при отправке сообщения пользователю: {te}")
    else:
        # Чат не активен, отправляем уведомление пользователю
        try:
            context.bot.send_message(
                chat_id=chat_id,
                text="Этот чат в данный момент не мониторится системой MoodMeter."
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке уведомления пользователю: {te}")

        # Логирование этого случая
        logger.info(f"Чат с ID {chat_id} не активен. Сообщение от пользователя {user.full_name} игнорировано.")


def start(update: Update, context: CallbackContext) -> None:
    """
    Отправляет приветственное сообщение с инструкциями.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    update.message.reply_text(
        "Привет! Добро пожаловать в бота MoodMeter. Вот доступные команды:\n\n"
        "1. /add_user — добавить ваш user_id.\n"
        "2. /add_chat chat_id [chat_name] — добавить чат в MoodMeter. Если не указать имя, оно будет пустое.\n"
        "3. /deactivate_chat chat_id — удалить чат из MoodMeter.\n"
        "4. /rename_chat chat_id new_chat_name — переименовать чат в MoodMeter.\n"
        "5. /help — вывести список команд.\n\n"
        "Важно: после команды указывайте chat_id через пробел!"
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """
    Отправляет список доступных команд и их описание.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    help_text = (
        "Вот доступные команды:\n\n"
        "/start — приветственное сообщение и инструкции.\n"
        "/add_user — зарегистрировать ваш user_id.\n"
        "/add_chat chat_id [chat_name] — добавить чат в MoodMeter. Если не указать имя, оно будет пустое.\n"
        "/deactivate_chat chat_id — деактивировать чат в MoodMeter.\n"
        "/rename_chat chat_id new_chat_name — переименовать чат в MoodMeter.\n"
        "/help — вывести этот список команд."
    )
    update.message.reply_text(help_text)


def add_user_command(update: Update, context: CallbackContext) -> None:
    """
    Обрабатывает команду /add_user для регистрации пользователя.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    if update.effective_chat.type != 'private':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Эта команда доступна только в личных сообщениях.'
        )
        return

    user_id = update.message.from_user.id
    password = hash_password(str(user_id))

    query_user = "SELECT user_id FROM public.user_credentials WHERE user_id=%s"

    try:
        users = conn.read_data_to_dataframe(query_user, (user_id,))

        if users.empty:
            save_user_to_sql(user_id, password)
            update.message.reply_text(f"Ваш user_id: {user_id} был успешно зарегистрирован.")
        else:
            update.message.reply_text(f"Ваш user_id: {user_id} уже зарегистрирован в системе.")
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Произошла ошибка при регистрации пользователя. Пожалуйста, попробуйте позже.'
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")


def add_chat_command(update: Update, context: CallbackContext) -> None:
    """
    Обрабатывает команду /add_chat для добавления чата в систему.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    if update.effective_chat.type != 'private':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Эта команда доступна только в личных сообщениях.'
        )
        return

    if len(context.args) == 0:
        update.message.reply_text('Укажите ID чата и название через пробел после команды.')
        return

    try:
        user_id = update.message.from_user.id
        chat_id = int(context.args[0])
        chat_name = context.args[1] if len(context.args) >= 2 else ''
    except ValueError:
        update.message.reply_text('ID чата должен быть числом.')
        return

    # Проверка наличия чата в базе данных
    query_chat = "SELECT status FROM public.chat WHERE chat_id = %s"
    try:
        chat_data = conn.read_data_to_dataframe(query_chat, (chat_id,))
    except Exception as e:
        logger.error(f"Ошибка при проверке чата в базе данных: {e}")
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Произошла ошибка при проверке чата. Пожалуйста, попробуйте позже.'
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")
        return

    try:
        if chat_data.empty:
            # Добавление нового чата
            conn.insert_data([(chat_id, 'active', chat_name)], 'chat', ['chat_id', 'status', 'chat_name'])
            save_chat_to_sql(user_id, chat_id)
            update.message.reply_text(f'Чат с ID {chat_id} и названием "{chat_name}" создан и активирован.')
        else:
            chat_status = chat_data.iloc[0]['status']
            if chat_status == 'deactivated':
                # Активация чата
                conn.update_data('chat', 'chat_id', chat_id, 'status', 'active')
                update.message.reply_text(f'Чат с ID {chat_id} был активирован.')

            # Проверка, привязан ли пользователь к чату
            query_user_chat = "SELECT user_id FROM public.user_chat WHERE chat_id = %s AND user_id = %s"
            user_chat_data = conn.read_data_to_dataframe(query_user_chat, (chat_id, user_id))

            if user_chat_data.empty:
                save_chat_to_sql(user_id, chat_id)
                update.message.reply_text(f'Вы добавлены в чат с ID {chat_id}.')
            else:
                update.message.reply_text(f'Вы уже привязаны к чату с ID {chat_id}.')
    except Exception as e:
        logger.error(f"Ошибка при добавлении чата: {e}")
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Произошла ошибка при добавлении чата. Пожалуйста, попробуйте позже.'
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")


def deactivate_chat_command(update: Update, context: CallbackContext) -> None:
    """
    Обрабатывает команду /deactivate_chat для деактивации чата в системе.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    if update.effective_chat.type != 'private':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Эта команда доступна только в личных сообщениях.'
        )
        return

    if len(context.args) < 1:
        update.message.reply_text('Укажите ID чата через пробел после команды.')
        return

    try:
        user_id = update.message.from_user.id
        chat_id = int(context.args[0])
    except ValueError:
        update.message.reply_text('ID чата должен быть числом.')
        return

    # Проверка, является ли пользователь администратором чата
    query_admin = "SELECT user_id FROM public.user_chat WHERE chat_id = %s"
    try:
        admin_data = conn.read_data_to_dataframe(query_admin, (chat_id,))
    except Exception as e:
        logger.error(f"Ошибка при проверке администратора чата: {e}")
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Произошла ошибка при проверке администратора чата. Пожалуйста, попробуйте позже.'
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")
        return

    if admin_data.empty or user_id not in admin_data['user_id'].values:
        update.message.reply_text('Вы не являетесь администратором этого чата.')
        return

    try:
        # Деактивация чата
        deactivate_chat_in_sql(chat_id)
        update.message.reply_text(f'Чат с ID {chat_id} был деактивирован в MoodMeter.')
    except Exception as e:
        logger.error(f"Ошибка при деактивации чата: {e}")
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Произошла ошибка при деактивации чата. Пожалуйста, попробуйте позже.'
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")


def rename_chat_command(update: Update, context: CallbackContext) -> None:
    """
    Обрабатывает команду /rename_chat для переименования чата в системе.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    if update.effective_chat.type != 'private':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Эта команда доступна только в личных сообщениях.'
        )
        return

    if len(context.args) != 2:
        update.message.reply_text('Укажите ID чата и новое название через пробел после команды.')
        return

    try:
        user_id = update.message.from_user.id
        chat_id = int(context.args[0])
        new_chat_name = context.args[1]
    except ValueError:
        update.message.reply_text('ID чата должен быть числом.')
        return

    # Проверка, является ли пользователь администратором чата
    query_admin = "SELECT user_id FROM public.user_chat WHERE chat_id = %s"
    try:
        admin_data = conn.read_data_to_dataframe(query_admin, (chat_id,))
    except Exception as e:
        logger.error(f"Ошибка при проверке администратора чата: {e}")
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Произошла ошибка при проверке администратора чата. Пожалуйста, попробуйте позже.'
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")
        return

    if admin_data.empty or user_id not in admin_data['user_id'].values:
        update.message.reply_text('Вы не являетесь администратором этого чата.')
        return

    try:
        # Смена имени
        conn.update_data('chat', 'chat_id', chat_id, 'chat_name', new_chat_name)
        update.message.reply_text(f'Чат с ID {chat_id} был переименован на "{new_chat_name}".')
    except Exception as e:
        logger.error(f"Ошибка при переименовании чата: {e}")
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Произошла ошибка при переименовании чата. Пожалуйста, попробуйте позже.'
            )
        except TelegramError as te:
            logger.error(f"Ошибка при отправке сообщения пользователю: {te}")


def send_alerts(context: CallbackContext) -> None:
    """Отправляет алерты пользователям при достижении критических значений настроения."""
    try:
        query_alert = """
        SELECT chat_id, uc.user_id, chat_name, 
               AVG(
                   CASE 
                       WHEN message_label = 'POSITIVE' THEN 1
                       WHEN message_label = 'NEGATIVE' THEN -1
                       ELSE 0
                   END
               ) AS avg_score,
               COUNT(*) AS message_count
        FROM public.message_analysis AS msg
        JOIN public.user_chat AS uc USING(chat_id)
        JOIN public.chat AS c USING(chat_id)
        WHERE message_datetime >= NOW() - INTERVAL '1 hour'
        GROUP BY chat_id, uc.user_id, chat_name
        """
        data_alert = conn.read_data_to_dataframe(query_alert)

        for _, row in data_alert.iterrows():
            user_id = row['user_id']
            chat_name = row['chat_name']
            avg_score = row['avg_score']
            message_count = row['message_count']

            # Определяем пороговое значение в зависимости от количества сообщений
            if 1 <= message_count <= 10:
                threshold = -0.7
            elif 11 <= message_count <= 50:
                threshold = -0.5
            elif message_count >= 51:
                threshold = -0.3
            else:
                # Если сообщений меньше 1, не отправляем алерт
                continue

            if avg_score <= threshold:
                message = (
                    f"⚠️ Внимание!\n\n"
                    f"Среднее настроение в чате '{chat_name}' за последний час опустилось до {avg_score:.2f} при количестве сообщений {message_count}."
                )
                try:
                    context.bot.send_message(chat_id=user_id, text=message)
                except TelegramError as te:
                    logger.error(f"Ошибка при отправке алерта пользователю {user_id}: {te}")
    except Exception as e:
        logger.error(f"Ошибка при отправке алертов: {e}")


def help_command(update: Update, context: CallbackContext) -> None:
    """
    Отправляет список доступных команд и их описание.

    Args:
        update (Update): Объект обновления от Telegram.
        context (CallbackContext): Контекст бота.
    """
    help_text = (
        "Вот доступные команды:\n\n"
        "/start — приветственное сообщение и инструкции.\n"
        "/help — вывести этот список команд.\n"
        "/add_user — зарегистрировать ваш user_id.\n"
        "/add_chat chat_id [chat_name] — добавить чат в MoodMeter. Если не указать имя, оно будет пустое.\n"
        "/deactivate_chat chat_id — деактивировать чат в MoodMeter.\n"
        "/rename_chat chat_id new_chat_name — переименовать чат в MoodMeter.\n\n"
        "Важно: после команды указывайте chat_id через пробел!"
    )
    update.message.reply_text(help_text)


def main() -> None:
    """
    Инициализирует бота и запускает обработку сообщений.
    """
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчики команд и сообщений
    job_queue = updater.job_queue
    job_queue.run_repeating(send_alerts, interval=3600, first=0)  # Отправляет алерты каждый час

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('add_user', add_user_command))
    dispatcher.add_handler(CommandHandler('add_chat', add_chat_command))
    dispatcher.add_handler(CommandHandler('deactivate_chat', deactivate_chat_command))
    dispatcher.add_handler(CommandHandler('rename_chat', rename_chat_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    try:
        updater.start_polling()
        logger.info("Бот запущен и работает.")
        updater.idle()
    except TelegramError as te:
        logger.error(f"Ошибка при запуске бота: {te}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при запуске бота: {e}")


if __name__ == '__main__':
    main()
