from etl_process import FetchDatasetList, FetchData, CleanData, ExtractMarketCloseDate
from random_stock_select import MonkeySelectStock
import time
import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import firestore
import json
from datetime import datetime
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time
import random
import plotly.express as px
import os

dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
key_path = os.path.join(dir_path, "secret_info/stockaroo-privatekey.json")




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
    stock_id_l = FetchDatasetList("stock", key_path)

    option = st.selectbox(
        "Stock List",
        stock_id_l
    )

    data = FetchData("stock", option, key_path)
    data_all = CleanData(data)
    close_days = ExtractMarketCloseDate(data_all)
    

    
    genre_duration = st.radio(
        "請選擇繪圖日期長度",
        ["1月", "3月", "5月", "1年", "5年", "全部時間"],
        horizontal=True
        )

    if genre_duration == '1月':
        data_part = FilterDate(data_all, 0)
    elif genre_duration == '3月':
        data_part = FilterDate(data_all, 1)
    elif genre_duration == '5月':
        data_part = FilterDate(data_all, 2)
    elif genre_duration == '1年':
        data_part = FilterDate(data_all, 3)
    elif genre_duration == '5年':
        data_part = FilterDate(data_all, 4)
    else:
        data_part = FilterDate(data_all, 5)

    line = go.Scatter(
        x=data_part["date"],
        y=data_part["close"],
        mode="lines"
    )
    fig = go.Figure()
    fig.add_trace(line)
    
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
        new_balances, new_balances_0050, dates, profit_ratioss, stockss = MonkeySelectStock(start_date, end_date, num_stock, 100000)
        df_plot = pd.DataFrame({
            "balance" : new_balances,
            "balance_0050" : new_balances_0050,
            "date" : dates
        })

        fig = px.line(df_plot, x="date", y=["balance", "balance_0050"], title="Balance of Randomly Selected Stock")
        st.plotly_chart(fig)
        
        df_detail_info = ModifyDetailDf(stockss, profit_ratioss)
        df_detail_info["結束日期"] = dates[1:]
        cols = df_detail_info.columns.to_list()
        new_column_order = ["結束日期"]
        for i in range(len(cols[:-1])):
            new_column_order.append(cols[i])
        df_detail_info = df_detail_info[new_column_order]
        st.markdown(css+df_detail_info.to_html(escape=False, index=False), unsafe_allow_html=True)

