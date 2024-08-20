import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import streamlit_authenticator as stauth

###Authenticator###
usernames = ['admin1', 'admin2']
names = ['Admin One', 'Admin Two']
passwords = ['admin', 'admin']

hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": hashed_passwords[0]},
        usernames[1]: {"name": names[1], "password": hashed_passwords[1]},
    }
}

authenticator = stauth.Authenticate(credentials, "app_home", "auth", cookie_expiry_days=30)


st.sidebar.title("User Management")
auth_option = st.sidebar.radio("Choose an option", options=["Login", "Register"])

if auth_option == "Login":
    print(credentials['usernames'].keys())
    name, authentication_status, username = authenticator.login('main')

    if authentication_status == False:
        st.error("Username/password is incorrect")
    elif authentication_status == None:
        st.warning("Please enter your username and password")
    elif authentication_status:
        ######################
        print(f'username: {username}, name: {name}')

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

        authenticator.logout("Logout")

elif auth_option == "Register":
    # Регистрация новых пользователей
    st.header("Register a New User")

    new_username = st.text_input("Enter a username")
    new_name = st.text_input("Enter your full name")
    new_password = st.text_input("Enter a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")

    if st.button("Register"):
        if new_password == confirm_password:
            hashed_new_password = stauth.Hasher([new_password]).generate()[0]
            credentials["usernames"].update({
                new_username: {"name": new_name, "password": hashed_new_password}
            })
            st.success("Registration successful! You can now log in.")
        else:
            st.error("Passwords do not match. Please try again.")
