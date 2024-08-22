import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from lib.postgresql_manager import PostgreSQLConnector
import hashlib
import time
import os
import subprocess

conn = PostgreSQLConnector()


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


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "token_entered" not in st.session_state:
    st.session_state["token_entered"] = False

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

elif not st.session_state["token_entered"]:
    st.title("Telegram Bot Configuration")

    token = st.text_input("Enter your Telegram Bot TOKEN", type="password")

    if st.button("Submit TOKEN"):
        if token:
            st.session_state["telegram_token"] = token
            st.session_state["token_entered"] = True

            env = os.environ.copy()
            env['TELEGRAM_TOKEN'] = token
            st.session_state['bot_process'] = subprocess.Popen(['python', 'telegram_bot.py'], env=env)

            st.success("Bot started successfully!")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Please enter a valid Telegram Bot TOKEN.")

else:
    mood_map = {
        'POSITIVE': 1,
        'NEGATIVE': -1,
        'NEUTRAL': 0
    }

    df = pd.read_json('generated_records.json')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    df['label_value'] = df['label'].map(mood_map)

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
