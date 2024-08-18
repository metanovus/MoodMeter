import streamlit as st
import pandas as pd
import plotly.graph_objs as go

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
    resampled_df = filtered_df.resample('H')['label_value'].mean()
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
