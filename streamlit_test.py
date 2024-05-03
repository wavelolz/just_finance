
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
import plotly.graph_objects as go
import os
import json

def load_config(db_name):
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_path = os.path.join(dir_path, "secret_info/config.json")
    with open(config_path, 'r') as file:
        config = json.load(file)

    if db_name == "raw":
        return config[0]
    elif db_name == "test":
        return config[1]
    
def GetConnection():
    config = load_config("test")
    db_connection = mysql.connector.connect(
    host=config["host"],
    user=config["user"],
    password=config["password"],
    database=config["database"]
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

def PrepareData(data):
    candle = data[["date", "Trading_Volume", "open", "close", "max", "min"]]
    candle.columns = ["date", "volume", "open", "close", "high", "low"]

    return candle


def FilterDate(candle_data, code):
    if code == 0:
        filter_candle_data = candle_data[-30:]
    elif code == 1:
        filter_candle_data = candle_data[-90:]
    elif code == 2:
        filter_candle_data = candle_data[-150:]
    elif code == 3:
        filter_candle_data = candle_data[-365:]
    elif code == 4:
        filter_candle_data = candle_data[-1825:]
    else:
        return candle_data
    return filter_candle_data


stock_id_l = FetchDatasetList()

option = st.selectbox(
    "Stock List",
    stock_id_l
)

data = FetchData(option)
data = CleanData(data)
candle_data_all = PrepareData(data)

genre_duration = st.radio(
    "請選擇繪圖日期長度",
    ["1月", "3月", "5月", "1年", "5年", "全部時間"],
    horizontal=True
    )

if genre_duration == '1月':
    candle_data_part = FilterDate(candle_data_all, 0)
elif genre_duration == '3月':
    candle_data_part = FilterDate(candle_data_all, 1)
elif genre_duration == '5月':
    candle_data_part = FilterDate(candle_data_all, 2)
elif genre_duration == '1年':
    candle_data_part = FilterDate(candle_data_all, 3)
elif genre_duration == '5年':
    candle_data_part = FilterDate(candle_data_all, 4)
else:
    candle_data_part = FilterDate(candle_data_all, 5)


candle = go.Candlestick(
    x=candle_data_part["date"], 
    open=candle_data_part["open"], 
    high=candle_data_part["high"], 
    low=candle_data_part["low"], 
    close=candle_data_part["close"]
    )

fig = go.Figure(data=candle)
st.plotly_chart(fig)



