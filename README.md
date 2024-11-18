# 🎭 MoodMeter: Анализ настроений в Telegram-чате

![Пример интерфейса](https://i.imghippo.com/files/ihsi8695Dg.jpg)

### Mood over Time (Days)
График показывает динамику изменения настроения с течением времени:
- 🟢 Положительное настроение.
- 🔴 Отрицательное настроение.

### Message Count by Label (Days)
График визуализирует количество сообщений, распределённых по меткам настроения:
- 🔴 Негативные.
- 🟢 Позитивные.
- ⚪ Нейтральные.

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
- [Вадим Самойлов](https://github.com/metanovus): Telegram-бот, Sentiment analysis, интерфейс, документация.
- [Михаил Иаковлев](https://github.com/miakovlev): Оптимизация, контейнеризация, тестирование, работа с БД
- [Вячеслав Ровенский](https://github.com/Viacheslav-Rovenskiy): участие в архитектурных решениях, разработка компонентов.
- [Николай Ответчиков](https://github.com/otvet4ikov): Анализ и архитектура проекта, тестирование

## ⚙️ Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/username/MoodMeter.git
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
