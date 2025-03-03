# 🎭 MoodMeter: Анализ настроений в Telegram-чате
*Начало проекта: Август 2024 | Презентация: Октябрь 2024*

![Mood over Time](https://i.imghippo.com/files/ihsi8695Dg.jpg "График Mood over Time (Days) показывает динамику настроения: 
🟢 Положительное, 
🔴 Отрицательное.
График Message Count by Label (Days) визуализирует количество сообщений по меткам:
🔴 Негативные.
🟢 Позитивные.
⚪ Нейтральные.")
<sub>*Для получения описания графика наведите мышкой на изображение*</sub>

## 📋 Описание
MoodMeter анализирует настроения в чате с помощью ML, классифицируя сообщения на позитивные, нейтральные и негативные. Построен на **Python**, **Hugging Face Transformers**, **Heroku** и **Streamlit**. Проект построен в рамках <img src="https://github.com/user-attachments/assets/d8cfb954-f366-4021-a90e-88e8850eeb8e" alt="karpov.courses" width="16"> [симулятора Data Science](https://karpov.courses/simulator-ds).

## 🏗️ Архитектура
- **Сбор данных**: API-интеграция для получения сообщений, сохранение в PostgreSQL.
- **Анализ**: Классификация сообщений моделью 🤗 [rubert-base-cased-sentiment-rurewiews](https://huggingface.co/blanchefort/rubert-base-cased-sentiment-rurewiews).
- **Визуализация**: Дашборды на Streamlit с использованием Plotly.

## 🛠️ Технологии
<p align="center">
  <a href="https://go-skill-icons.vercel.app/">
    <img src="https://go-skill-icons.vercel.app/api/icons?i=linux,python,pycharm,huggingface,postgres,docker,streamlit,heroku,pandas&theme=dark"/>
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
- [Вадим Самойлов](https://github.com/metanovus): [Telegram-бот](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/services/telegram_bot.py), [Sentiment analysis](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/modules/transformers_mood.py), [интерфейс](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/services/dashboard.py), документация.
- [Михаил Иаковлев](https://github.com/miakovlev): [Оптимизация](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/utils/utils.py), [контейнеризация](https://github.com/metanovus/MoodMeter/blob/main/docker-compose.yml), [работа с БД](https://github.com/metanovus/MoodMeter/blob/main/lib/postgresql_manager.py), [создание метрики](https://github.com/metanovus/MoodMeter/blob/main/moodmeter/modules/mood_calculator.py), тестирование
- [Вячеслав Ровенский](https://github.com/Viacheslav-Rovenskiy): Участие в архитектурных решениях, доработка различных компонентов.
- [Николай Ответчиков](https://github.com/otvet4ikov): Анализ и архитектура проекта, тестирование, доработка различных компонентов.

## ⚙️ Системные требования и установка
Для работы приложения потребуется:
- установленная Unix-подобная ОС.
- готовый Telegram-бот.
- подготовленная PostgreSQL база данных (например, Heroku).

Порядок установки:
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
   # необходимо вбить данные для вашей базы данных (PostreSQL)
   # разработка и тестирование велись на Heroku
   
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
