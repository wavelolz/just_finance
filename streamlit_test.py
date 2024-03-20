#%%
import time
import streamlit as st
st.set_page_config(layout="wide")
import numpy as np
import pandas as pd
from FinMind.data import DataLoader
import ta
from ta.utils import dropna
import mysql.connector
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import mplfinance as mpf

#%%


def GetConnection():
    db_connection = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="@Fk10150305msds",
    database="test"
    )
    return db_connection

def FetchDatasetList():
    conn = GetConnection()
    cursor = conn.cursor()
    query = "select table_name from information_schema.tables where table_schema = 'test';"
    cursor.execute(query)
    result = cursor.fetchall()
    stock_id_l = [i[0] for i in result]
    return stock_id_l

def FetchData(stock_id):
    conn = GetConnection()
    cursor = conn.cursor()
    query_data = f"select * from test.{stock_id}"
    cursor.execute(query_data)
    data = pd.DataFrame(cursor.fetchall())

    query_colnames = f"select distinct column_name from information_schema.columns where table_schema = 'test';"
    cursor.execute(query_colnames)
    colname = cursor.fetchall()
    colname = [i[0] for i in colname]
    data.columns = colname
    return data

def CleanData(data):
    filter_data = data.loc[data["close"] != 0]
    return filter_data

def FilterDate(data, code):
    if code == 0:
        filter_data = data.iloc[-30:]
    elif code == 1:
        filter_data = data.iloc[-90:]
    elif code == 2:
        filter_data = data.iloc[-150:]
    elif code == 3:
        filter_data = data.iloc[-365:]
    elif code == 4:
        filter_data = data.iloc[-1825:]
    else:
        return data
    return filter_data

def ExtractTick(data):
    n = len(data)
    tick = np.linspace(0, n-1, 6)
    tick = [int(i) for i in tick]
    filter_data = data.iloc[tick, :]
    tick_label = filter_data["date"].to_list()
    return [tick, tick_label]

def GenerateColor(data):
    close = data["close"].to_list()
    colorList = ["blue"]
    for i in range(1, len(close), 1):
        if close[i] > close[i-1]:
            colorList.append("red")
        elif close[i] == close[i-1]:
            colorList.append("purple")
        else:
            colorList.append("green")
    return colorList 

stock_id_l = FetchDatasetList()

option = st.selectbox(
    "Stock List",
    stock_id_l
)

data = FetchData("s0050")
data = CleanData(data)

#%%
data_filter = data[:50]
plot_data = data_filter[["date", "Trading_Volume", "open", "close", "max", "min"]]
plot_data.columns = ["Date", "Volume", "Open", "Close", "High", "Low"]
plot_data.index = pd.to_datetime(plot_data["Date"])
plot_data = plot_data.drop(["Date"], axis=1)
plot_data = plot_data[["Open", "High", "Low", "Close", "Volume"]]
mc = mpf.make_marketcolors(up="r", down="g")
s = mpf.make_mpf_style(marketcolors=mc)
mpf.plot(plot_data, type="candle", volume=True, style=s)
#%%

# st.write(data)

genre = st.radio(
    "請選擇繪圖日期長度",
    ["1月", "3月", "5月", "1年", "5年", "全部時間"],
    horizontal=True
    )

if genre == '1月':
    plot_data = FilterDate(data, 0)
elif genre == '3月':
    plot_data = FilterDate(data, 1)
elif genre == '5月':
    plot_data = FilterDate(data, 2)
elif genre == '1年':
    plot_data = FilterDate(data, 3)
elif genre == '5年':
    plot_data = FilterDate(data, 4)
else:
    plot_data = FilterDate(data, 5)


tick, tick_label = ExtractTick(plot_data)
bar_color = GenerateColor(plot_data)

st.write(plot_data)
fig, (ax1, ax2, ax3) = plt.subplots(figsize = (8, 12), nrows=3, ncols=1, height_ratios=[4, 1, 3])
ax1.plot(plot_data["date"], plot_data["close"])
ax1.grid(True)
ax1.set_xticks(tick)
ax1.set_xticklabels(tick_label)

x = np.arange(len(plot_data["date"]))
ax1.plot(x, plot_data["SMA5"], label="SMA5")
ax1.plot(x, plot_data["SMA10"], label="SMA10")
ax1.plot(x, plot_data["SMA120"], label="SMA120")
ax1.legend()

ax2.bar(x, plot_data["Trading_Volume"], color=bar_color)
ax2.set_xticks(tick)
ax2.set_xticklabels(tick_label)
plt.tight_layout()
st.pyplot(fig)


