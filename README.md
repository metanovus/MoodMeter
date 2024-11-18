# 🎭 MoodMeter: Анализ настроений в Telegram-чате

<sub>*Для получения описания графика, наведите мышкой на изображение*</sub>

![Mood over Time](https://i.imghippo.com/files/ihsi8695Dg.jpg "График Mood over Time (Days) показывает динамику настроения: 
🟢 Положительное, 
🔴 Отрицательное.
График Message Count by Label (Days) визуализирует количество сообщений по меткам:
🔴 Негативные.
🟢 Позитивные.
⚪ Нейтральные.")

## 📋 Описание
MoodMeter анализирует настроения в чате с помощью ML, классифицируя сообщения на позитивные, нейтральные и негативные. Построен на **Python**, **Hugging Face Transformers**, **Heroku** и **Streamlit**.

## 🏗️ Архитектура
- **Сбор данных**: API-интеграция для получения сообщений, сохранение в PostgreSQL.
- **Анализ**: Классификация сообщений моделью 🤗 [rubert-base-cased-sentiment-rurewiews](https://huggingface.co/blanchefort/rubert-base-cased-sentiment-rurewiews).
- **Визуализация**: Дашборды на Streamlit с использованием Plotly.

## 🛠️ Технологии
<p align="center">
  <a href="https://go-skill-icons.vercel.app/">
    <img src="https://go-skill-icons.vercel.app/api/icons?i=python,pycharm,huggingface,postgres,docker,streamlit,pandas&theme=dark"/>
  </a>
</p>

- Python 3.11
- Hugging Face Transformers
- Heroku (PostgreSQL)
- Streamlit
- Plotly
- Telegram API
- Docker

## 👥 Команда
- [Вадим Самойлов](https://github.com/metanovus): [Telegram-бот](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/services/dashboard.py), [Sentiment analysis](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/modules/transformers_mood.py), [интерфейс](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/services/telegram_bot.py), документация.
- [Михаил Иаковлев](https://github.com/miakovlev): [Оптимизация](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/utils/utils.py), [контейнеризация](https://github.com/metanovus/MoodMeter/blob/main/docker-compose.yml), [работа с БД](https://github.com/metanovus/MoodMeter/blob/main/lib/postgresql_manager.py), тестирование
- [Вячеслав Ровенский](https://github.com/Viacheslav-Rovenskiy): Участие в архитектурных решениях, доработка различных компонентов
- [Николай Ответчиков](https://github.com/otvet4ikov): Анализ и архитектура проекта, тестирование

## ⚙️ Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/metanovus/MoodMeter.git
   cd MoodMeter
   ```
2. Установите Python 3.11
   ```bash
   sudo apt install python3.11
   python3 --version  # убедитесь, что версия 3.11 существует
   ```
2. Установите зависимости системы:
   ```bash
   sudo apt install libpq-dev python3-dev
   ```

4. Создайте и активируйте виртуальное окружение:
   ```bash
   python3.11 -m venv myenv
   source myenv/bin/activate
   ```

5. Запустите зависимости Python:
   ```bash
   pip install -r requirements-bot.txt
   pip install -r requirements-streamlit.txt
   ```
6. Настройте окружение:
   ```bash
   HOST=
   DATABASE=
   USERSQL=
   PORT=
   PASSWORD=
    
   TELEGRAM_TOKEN=
   ADMIN_CHAT_ID=
   ```
7. Запустите приложение:
   ```bash
   streamlit run moodmeter/services/dashboard.py
   ```
8. Запустите Telegram бота:
   ```bash
   python3 moodmeter/services/telegram_bot.py
   ```

## 💡 Применение
- Анализ настроений в чатах.
- Мониторинг проблемных тем.
- Визуализация трендов для улучшения клиентского опыта. 
