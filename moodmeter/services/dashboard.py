import time
from typing import List, Optional

import pandas as pd
import plotly.graph_objs as go
import streamlit as st

from lib.postgresql_manager import PostgreSQLConnector
from moodmeter.utils.utils import hash_password

# Инициализация подключения к базе данных
conn = PostgreSQLConnector()

# Отображение заголовка приложения
st.title("MoodMeter Dashboard")

# Словарь для преобразования меток настроения в числовые значения
MOOD_MAP = {
    'POSITIVE': 1,
    'NEGATIVE': -1,
    'NEUTRAL': 0
}


def authenticate_user(username: str, password: str) -> bool:
    """
    Аутентифицирует пользователя, сравнивая захешированный пароль из БД с введенным паролем.

    Args:
        username (str): Имя пользователя.
        password (str): Введенный пароль.

    Returns:
        bool: True, если аутентификация успешна, иначе False.
    """
    query = "SELECT password FROM user_credentials WHERE user_id = %s"
    try:
        result = conn.read_data(query, (username,))
        if result:
            stored_hashed_password = result[0][0]
            return hash_password(password) == stored_hashed_password
        return False
    except Exception as e:
        # Здесь можно добавить логирование ошибки
        return False


def get_user_id(username: str) -> Optional[int]:
    """
    Получает user_id, связанный с заданным именем пользователя.

    Args:
        username (str): Имя пользователя.

    Returns:
        Optional[int]: user_id, если найден, иначе None.
    """
    query = "SELECT user_id FROM user_credentials WHERE user_id = %s"
    result = conn.read_data(query, (username,))
    if result:
        return result[0][0]
    return None


def get_user_chats(user_id: int) -> List[int]:
    """
    Получает список активных chat_id, связанных с пользователем.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        List[int]: Список chat_id.
    """
    query = """
        SELECT uc.chat_id
        FROM user_chat uc
        JOIN chat c ON uc.chat_id = c.chat_id
        WHERE uc.user_id = %s AND c.status = 'active'
    """
    result = conn.read_data(query, (user_id,))
    return [row[0] for row in result]


def load_message_data(chat_id: int) -> pd.DataFrame:
    """
    Загружает данные сообщений для заданного chat_id.

    Args:
        chat_id (int): Идентификатор чата.

    Returns:
        pd.DataFrame: Датафрейм с данными сообщений.
    """
    query = """
        SELECT message_datetime, chat_id, message_label
        FROM message_analysis
        WHERE chat_id = %s
    """

    data = conn.read_data(query, (chat_id,))
    df = pd.DataFrame(data, columns=['date', 'chat_id', 'label'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df['label_value'] = df['label'].map(MOOD_MAP)

    return df


def main():
    # Проверяем, аутентифицирован ли пользователь
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("Login")

        # Поля для ввода имени пользователя и пароля
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate_user(username, password):
                st.success("Welcome")
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                time.sleep(2)
                st.rerun()  # Перезапускаем скрипт после аутентификации
            else:
                st.error("Username/password is incorrect")

    else:
        # Пользователь аутентифицирован
        user_id = get_user_id(st.session_state["username"])
        if user_id is None:
            st.error("User ID not found.")
        else:
            # Получаем список chat_id для этого пользователя
            user_chats = get_user_chats(user_id)

            if not user_chats:
                st.error("No chats found for this user.")
            else:
                # Выбор чата из доступных
                chat_id = st.sidebar.selectbox("Select Chat", options=user_chats)

                # Загружаем данные сообщений для выбранного чата
                df = load_message_data(chat_id)

                if df.empty:
                    st.warning("No data available for the selected chat.")

                    fig = go.Figure()

                    st.title("Mood grouping by time interval")
                    st.plotly_chart(fig)
                else:
                    # Фильтрация по дате
                    st.sidebar.header("Filter by Date")
                    start_date = st.sidebar.date_input("Start date", df.index.min().date())
                    end_date = st.sidebar.date_input("End date", df.index.max().date())

                    # Фильтруем данные по выбранному диапазону дат
                    filtered_df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]

                    # Выбор интервала группировки
                    grouping = st.sidebar.selectbox(
                        'Choose interval for grouping:',
                        ['Hours', 'Days', 'Weeks']
                    )

                    # Ресемплирование данных на основе выбранного интервала
                    if grouping == 'Hours':
                        resampled_df = filtered_df.resample('h')['label_value'].mean()
                    elif grouping == 'Days':
                        resampled_df = filtered_df.resample('D')['label_value'].mean()
                    elif grouping == 'Weeks':
                        resampled_df = filtered_df.resample('W')['label_value'].mean()

                    # Создаем график
                    fig = go.Figure()

                    fig.add_trace(go.Bar(
                        x=resampled_df.index,
                        y=resampled_df.clip(lower=0),
                        name='Positive Mood',
                        marker_color='green'
                    ))

                    fig.add_trace(go.Bar(
                        x=resampled_df.index,
                        y=resampled_df.clip(upper=0),
                        name='Negative Mood',
                        marker_color='red'
                    ))

                    fig.update_layout(
                        title=f'Mood over Time ({grouping})',
                        xaxis_title='Time',
                        yaxis_title='Mood Score',
                        showlegend=False,
                        plot_bgcolor='white',
                        barmode='relative'
                    )

                    st.markdown(f"<h3>Mood grouping by {grouping.lower()}</h3>", unsafe_allow_html=True)
                    st.plotly_chart(fig)


if __name__ == "__main__":
    main()
