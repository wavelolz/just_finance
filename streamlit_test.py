
import time
import streamlit as st
# st.set_page_config(layout="wide")
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
import random
import plotly.express as px


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

def ExtractMarketCloseDate(data):
    date_l = data["date"].to_list()
    start_date = datetime.strptime(date_l[0], "%Y-%m-%d")
    end_date = datetime.strptime(date_l[-1], "%Y-%m-%d")
    diff = (end_date-start_date).days
    all_days = [str(start_date+timedelta(days=i)).split(" ")[0] for i in range(diff)]
    close_days = sorted(set(all_days)-set(date_l))
    return close_days


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


def GenerateRandomStockList(start_date, num_stock):
    result = {}
    while len(result) < num_stock:
        stock_id = random.sample(FetchDatasetList(), 1)[0]
        data = FetchData(stock_id)
        end_date_margin = str(datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=45))
        if data.iloc[0]["date"]<start_date and data.iloc[-1]["date"]>end_date_margin and stock_id not in list(result.keys()):
            result[f"{stock_id}"] = data
    return result

def GetDataInterval(data, start_date):
    end_date = str(datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=30))
    for key in list(data.keys()):
        full_data = data[f"{key}"]
        truncated_data = full_data.loc[(full_data["date"] >= start_date) & (full_data["date"] <= end_date)]
        data[f"{key}"] = truncated_data
    return data

def FindBuyPrice(df):
    for i in range(len(df)):
        if df.iloc[i]["Trading_Volume"] > 0:
            return df.iloc[i]['open']
    return np.NAN

def FindSellPrice(df):
    for i in range(len(df)-1, 0, -1):
        if df.iloc[i]["Trading_Volume"] > 0:
            return df.iloc[i]['open']
    return np.NAN

def ComputeProfit(data, balance):
    keys = list(data.keys())
    balance_for_each = balance // len(keys)
    buy_prices = [FindBuyPrice(data[keys[i]]) for i in range(len(keys))]
    sell_prices = [FindSellPrice(data[keys[i]]) for i in range(len(keys))]
    profits_per_share = np.array(sell_prices)-np.array(buy_prices)
    profit_ratios = np.round((profits_per_share / np.array(buy_prices))*100, 2)
    shares = np.array([balance_for_each // buy_prices[i] for i in range(len(buy_prices))])
    new_balance = np.sum(profits_per_share*shares) + balance
    return new_balance, profit_ratios

def MonkeySelectStock(start_date, end_date, num_stock, balance):
    new_balances = [balance]
    dates = [start_date]
    profit_ratioss = []
    stockss = []
    while str(start_date) <= end_date:
        full_data = GenerateRandomStockList(str(start_date).split(" ")[0], num_stock)
        truncated_data = GetDataInterval(full_data, str(start_date).split(" ")[0])
        new_balance, profit_ratios = ComputeProfit(truncated_data, balance)
        new_balances.append(new_balance)
        profit_ratioss.append(profit_ratios)
        stockss.append(list(full_data.keys()))
        start_date += timedelta(days=30)
        dates.append(start_date)
    return new_balances, dates, profit_ratioss, stockss

def ModifyDetailDf(stockss, profit_ratioss):
    infoss = []
    for i in range(len(stockss)):
        infos = []
        for j in range(len(stockss[i])):
            if profit_ratioss[i][j]>0:
                info = f"<p style='color: red;'>{stockss[i][j]}<br>▲{str(profit_ratioss[i][j])}%</p>"
            else:
                info = f"<p style='color: green;'>{stockss[i][j]}<br>▼{str(profit_ratioss[i][j])[1:]}%</p>"
            infos.append(info)
        infoss.append(infos)
    infoss = pd.DataFrame(infoss)
    colnames = [f"標的{i+1}" for i in range(len(stockss[0]))]
    infoss.columns = colnames
    return infoss

css = """
<style>
    table {
        width: 100%;
        table-layout: fixed;
        word-wrap: break-word;
    }
    th, td {
        padding: 10px;
        text-align: left;
    }
</style>
"""


tab_graph, tab_dollar_cost_averaging, tab_random_strategy = st.tabs(["個股走勢", "定期定額實驗", "隨機選股實驗"])

with tab_graph:
    stock_id_l = FetchDatasetList()

    option = st.selectbox(
        "Stock List",
        stock_id_l
    )

    data = FetchData(option)
    data = CleanData(data)
    candle_data_all = PrepareData(data)
    close_days = ExtractMarketCloseDate(candle_data_all)
    

    
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
    fig.update_xaxes(rangebreaks=[dict(values=close_days)])
    st.plotly_chart(fig, use_container_width=True)

with tab_dollar_cost_averaging:
    st.header("這裡做定期定額")



with tab_random_strategy:
    st.header("這裡做隨機選股")
    start_date = st.text_input("起始日期 YYYY-MM-DD")
    end_date = st.text_input("結束日期 YYYY-MM-DD")
    num_stock = st.selectbox("標的數量", [i+1 for i in range(8)])
    if st.button("Click to start"):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        new_balances, dates, profit_ratioss, stockss = MonkeySelectStock(start_date, end_date, num_stock, 100000)
        df_plot = pd.DataFrame({
            "balance" : new_balances,
            "date" : dates
        })
        fig = px.line(df_plot, x="date", y="balance", title="Balance of Randomly Selected Stock")
        st.plotly_chart(fig)
        
        df_detail_info = ModifyDetailDf(stockss, profit_ratioss)
        df_detail_info["結束日期"] = dates[1:]
        cols = df_detail_info.columns.to_list()
        new_column_order = ["結束日期"]
        for i in range(len(cols[:-1])):
            new_column_order.append(cols[i])
        df_detail_info = df_detail_info[new_column_order]
        st.markdown(css+df_detail_info.to_html(escape=False, index=False), unsafe_allow_html=True)

