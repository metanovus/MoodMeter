# 🎭 MoodMeter: Анализ настроений в Telegram-чате

![Пример интерфейса](https://i.imghippo.com/files/ihsi8695Dg.jpg)

## 📋 Описание
MoodMeter анализирует настроения в чате с помощью ML, классифицируя сообщения на позитивные, нейтральные и негативные. Построен на Python, Hugging Face Transformers, Heroku и Streamlit.

## 🏗️ Архитектура
- **Сбор данных**: Получение сообщений через API, сохранение в PostgreSQL
- **Анализ**: Использование модели 🤗 [blanchefort/rubert-base-cased-sentiment-rurewiews](https://huggingface.co/blanchefort/rubert-base-cased-sentiment-rurewiews)
- **Визуализация**: Интерактивные дашборды на Streamlit

## 🛠️ Технологии
- Python 3.11
- Hugging Face Transformers (+ PyTorch)
- Heroku (PostgreSQL)
- Streamlit
- Plotly
- Telegram API
- Docker

## 👥 Команда проекта

### [Вадим Самойлов](https://github.com/metanovus) - ML инженер
- Разработка Telegram-бота и интерфейса (Streamlit + Plotly)
- Тестирование и оценка ML моделей (dostoevsky, ruBERT)
- Реализация хранения данных (JSON → Heroku)
- Техническая документация и [дизайн-документ](https://crystalline-throat-711.notion.site/MoodScore-2-15c8445d66ae4951b30dfcb094f991df)

### [Михаил Иаковлев](https://github.com/miakovlev) - ML/DevOps инженер
- Оптимизация основных скриптов
- Интеграция и управление БД
- Тестирование в production
- Контейнеризация (Docker)
- Подготовка презентационных материалов

### [Вячеслав Ровенский](https://github.com/Viacheslav-Rovenskiy) - Data Scientist/Data Analyst
- Управление GitHub-репозиторием
- Исследование моделей sentiment analysis
- Разработка ключевых компонентов (бот, веб-интерфейс)
- Участие в архитектурных решениях

### [Николай Ответчиков](https://github.com/otvet4ikov) - Системный аналитик
- Валидация концепций проекта
- Участие в проектировании архитектуры
- Анализ и оценка технических решений

## ⚙️ Установка

### 1. Клонирование и настройка окружения
```bash
git clone https://github.com/username/MoodMeter.git
cd MoodMeter
python3.11 -m venv myenv
source myenv/bin/activate
```

### 2. Зависимости
```bash
sudo apt install libpq-dev python3-dev
pip install -r requirements-bot.txt
pip install -r requirements-streamlit.txt
```

### 3. Конфигурация
Создайте `.env`:
```bash
HOST=
DATABASE=
USERSQL=
PORT=
PASSWORD=
TELEGRAM_TOKEN=
ADMIN_CHAT_ID=
```

### 4. Запуск
```bash
streamlit run dashboard.py
python3 telegram_bot.py
```

## 💡 Применение
- Мониторинг настроений в чатах поддержки
- Анализ проблемных тем
- Визуализация трендов настроений
