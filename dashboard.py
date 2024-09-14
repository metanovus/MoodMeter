import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from lib.postgresql_manager import PostgreSQLConnector
import hashlib
import time

conn = PostgreSQLConnector()

MOOD_MAP = {
                'POSITIVE': 1,
                'NEGATIVE': -1,
                'NEUTRAL': 0
            }

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    query = "SELECT password FROM user_credentials WHERE user_id = %s"
    try:
        result = conn.read_data(query, (username,))
        if result:
            stored_hashed_password = result[0][0]
            return hash_password(password) == stored_hashed_password
        else:
            return False
    except Exception as e:
        # st.error(f"An error occurred: {e}")
        return False


def get_user_id(username):
    query = "SELECT user_id FROM user_credentials WHERE user_id = %s"
    result = conn.read_data(query, (username,))
    if result:
        return result[0][0]
    else:
        return None


def get_user_chats(user_id):
    query = "SELECT chat_id FROM user_chat WHERE user_id = %s"
    result = conn.read_data(query, (user_id,))
    return [row[0] for row in result]


def load_message_data(chat_id):
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


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(username, password):
            st.success(f"Welcome")
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            time.sleep(2)
            st.rerun()
        else:
            st.error("Username/password is incorrect")

else:

    user_id = get_user_id(st.session_state["username"])
    if user_id is None:
        st.error("User ID not found.")

    else:

        # Получаем список chat_id для этого пользователя
        user_chats = get_user_chats(user_id)

        if not user_chats:
            st.error("No chats found for this user.")

        else:
            # Добавляем фильтр для выбора чата
            chat_id = st.sidebar.selectbox("Select Chat", options=user_chats)



            df = load_message_data(chat_id)

            if df.empty:
                st.warning("No data available for the selected chat.")

                fig = go.Figure()

                st.title("Mood grouping by time interval")
                st.plotly_chart(fig)

            else:

                st.sidebar.header("Filter by Date")
                start_date = st.sidebar.date_input("Start date", df.index.min().date())
                end_date = st.sidebar.date_input("End date", df.index.max().date())

                filtered_df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]

                grouping = st.sidebar.selectbox(
                    'Choose interval for grouping:',
                    ['Hours', 'Days', 'Weeks']
                )

                if grouping == 'Hours':
                    resampled_df = filtered_df.resample('h')['label_value'].mean()
                elif grouping == 'Days':
                    resampled_df = filtered_df.resample('D')['label_value'].mean()
                elif grouping == 'Weeks':
                    resampled_df = filtered_df.resample('W')['label_value'].mean()

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

                st.title(f'Mood grouping by {grouping.lower()}')
                st.plotly_chart(fig)
