# Standard library imports
import time
import random
import os
from datetime import datetime, timedelta
import calendar
import json

# Third-party library imports
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import firestore

# Custom module imports
from etl_process import FetchDatasetList, FetchData, CleanData, ExtractMarketCloseDate
from random_stock_select import MonkeySelectStock

dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
key_path = os.path.join(dir_path, "secret_info/stockaroo-privatekey.json")


def filter_months(year, min_date, max_date):
    months = list(range(1, 13))
    if year == min_date.year and year == max_date.year:
        return list(range(min_date.month, max_date.month + 1))
    elif year == min_date.year:
        return list(range(min_date.month, 13))
    elif year == max_date.year:
        return list(range(1, max_date.month + 1))
    else:
        return months

def filter_quarters(year, min_date, max_date):
    quarter_month_map = {
    "Q1": (1, 3),
    "Q2": (4, 6),
    "Q3": (7, 9),
    "Q4": (10, 12)
    }
    valid_quarters = []
    for quarter, (start_month, end_month) in quarter_month_map.items():
        if ((year == min_date.year and end_month >= min_date.month) or year > min_date.year) and \
           ((year == max_date.year and start_month <= max_date.month) or year < max_date.year):
            valid_quarters.append(quarter)
    return valid_quarters

def calculate_investment_returns(filtered_data, duration_type, MIA=1000):
    if not filtered_data.empty:
        if duration_type == "Month":
            group_cols = ['year', 'month']
        elif duration_type == "Quarter":
            group_cols = ['year', 'quarter']
        elif duration_type == "Year":
            group_cols = ['year']
        
        first_days = filtered_data.groupby(group_cols).first().reset_index(drop=True)
        last_days = filtered_data.groupby(group_cols).last().reset_index(drop=True)
        
        # Initialize variables to store results
        durations = np.arange(len(first_days)) + 1  # Durations from 0 to the number of periods - 1

        # Calculate cumulative stock bought for each period
        opening_prices = first_days['open'].values
        closing_prices = last_days['close'].values

        cumulative_stock = np.cumsum(MIA / opening_prices)
        cost = np.cumsum([MIA] * len(opening_prices))
        revenue = np.round(cumulative_stock * closing_prices, 2)

        # Calculate the invested amount for each period
        invested_amounts = MIA * (durations)

        # Calculate profit ratios
        ROI = np.round((revenue - invested_amounts) / invested_amounts * 100, 2)
        
        # Return the results as a list of lists
        return [durations.tolist(), cost.tolist(), revenue.tolist(), ROI.tolist()]
    else:
        return [[], [], [], []]  # Return empty lists if filtered_data is empty

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
    # Set the title of the app
    st.title("Regular Investment Plan Simulation")
    st.subheader("Select Monthly Investment Account")

    # Create a text input widget for monthly investment amount
    user_input = st.text_input("Money you invest monthly", value=1000)
    MIA = int(user_input)  # Default to 1000 if no input

    # Add a select box for the stock code at the top
    stock_code = st.selectbox("Select Stock Code:", ["2609", "0050", "0052", "0053", "0054"])

    # Select duration type: month, quarter, or year
    duration_type = st.selectbox("Select Duration Type:", ["Month", "Quarter", "Year"])

    st.subheader("Select Starting and Ending Date")
    # Load the stock data file based on the selected stock code
    data = pd.read_csv(f'just_finance/Andy/s{stock_code}.csv')
    data0050 = pd.read_csv(f'just_finance/Andy/s0050.csv')
    data['date'] = pd.to_datetime(data['date'])
    data0050['date'] = pd.to_datetime(data0050['date'])

    # Extract month, quarter, and year
    data['month'] = data['date'].dt.month
    data['year'] = data['date'].dt.year
    data['quarter'] = data['date'].dt.to_period('Q')
    data0050['month'] = data0050['date'].dt.month
    data0050['year'] = data0050['date'].dt.year
    data0050['quarter'] = data0050['date'].dt.to_period('Q')

    # Quarter Dictionary
    quarter_month_map = {
    "Q1": (1, 3),
    "Q2": (4, 6),
    "Q3": (7, 9),
    "Q4": (10, 12)
    }

    # Find the max and min dates in the file
    min_date = data['date'].min()
    max_date = data['date'].max()

    # Get the years range based on the min and max dates
    years = list(range(min_date.year, max_date.year + 1))

    if duration_type == "Month":
        start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
        valid_start_months = filter_months(start_year, min_date, max_date)
        start_month = st.selectbox("Start Month:", valid_start_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))

        end_year = st.selectbox("End Year:", years, index=len(years) - 1)
        valid_end_months = filter_months(end_year, min_date, max_date)
        end_month = st.selectbox("End Month:", valid_end_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
        
    elif duration_type == "Quarter":
        start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
        valid_start_quarters = filter_quarters(start_year, min_date, max_date)
        start_quarter = st.selectbox("Start Quarter:", valid_start_quarters)

        end_year = st.selectbox("End Year:", years, index=len(years) - 1)
        valid_end_quarters = filter_quarters(end_year, min_date, max_date)
        end_quarter = st.selectbox("End Quarter:", valid_end_quarters)

        start_month = quarter_month_map[start_quarter][0]
        end_month = quarter_month_map[end_quarter][1]

    elif duration_type == "Year":
        start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
        end_year = st.selectbox("End Year:", years, index=len(years) - 1)

        start_month = 1
        end_month = 12

    if start_year and start_month and end_year and end_month:
        start_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 1) + pd.offsets.MonthEnd(1)
        if end_date in data['date'].values:
            end_date = end_date
        else:
            end_date = max(data['date'])
        # Filter the data based on the selected date range
        filtered_data = data.loc[(data['date'] >= start_date) & (data['date'] <= end_date)].copy()
        filtered_data0050 = data0050.loc[(data0050['date'] >= start_date) & (data0050['date'] <= end_date)].copy()

        duration, cost, revenue, ROI = calculate_investment_returns(filtered_data, duration_type, MIA)
        _, _, _, ROI0050 = calculate_investment_returns(filtered_data0050, duration_type, MIA)

        if duration_type == "Month":
            duration_label = 'Duration (Months)'
        elif duration_type == "Quarter":
            duration_label = 'Duration (Quarters)'
        elif duration_type == "Year":
            duration_label = 'Duration (Years)'

        result = pd.DataFrame({
            duration_label: duration,
            'Cost': cost,
            'Revenue': revenue,
            'Return on Investment (%)': ROI
        })

        st.subheader("Investment Summary Table")
        st.write(f"Investment Duration: {start_date.strftime(r'%Y-%m-%d')} to {end_date.strftime(r'%Y-%m-%d')}")
        st.markdown(f'<p style="color:gray; font-style:italic;">The ROI of Stock 0050 is {ROI0050[-1]} in this duration</p>', unsafe_allow_html=True)

        fig = go.Figure(data=go.Table(
            header=dict(values=list(result[[duration_label, 'Cost', 'Revenue', 'Return on Investment (%)']].columns),
                        fill_color='#FDBE72',
                        align='center'),
            cells=dict(values=[result[duration_label], result['Cost'], result['Revenue'], result['Return on Investment (%)']],
                        fill_color='#E5ECF6',
                        align='left'))
        )

        fig.update_layout(margin=dict(l=5, r=5, b=10, t=10),
                            paper_bgcolor='white')

        st.write(fig)
    
    else:
        st.write("No data available for the selected date range.")


with tab_random_strategy:
    st.header("這裡做隨機選股")
    start_date = st.text_input("起始日期 YYYY-MM-DD")
    end_date = st.text_input("結束日期 YYYY-MM-DD")
    num_stock = st.selectbox("標的數量", [i+1 for i in range(8)])
    if st.button("Click to start"):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        new_balances, new_balances_0050, dates, profit_ratioss, stockss = MonkeySelectStock(start_date, end_date, num_stock, 100000, key_path)
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

