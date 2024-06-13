from etl_process import FetchDatasetList, FetchData, FetchDateMargin
from datetime import datetime, timedelta
import random
import numpy as np
import os
import pandas as pd


def GenerateRandomStockList(start_date, num_stock, category, invest_interval, key_path):
    result = {}
    invest_interval_map = {
        "Month" : 45,
        "Quarter" : 105,
        "Year" : 380
    }
    stock_df = FetchDatasetList(key_path)

    if category == "All":
        stocks = stock_df["id"].to_list()
    else:
        stocks = stock_df.loc[stock_df["c"] == category]["id"].to_list()

    date_margin = FetchDateMargin(key_path)
    while len(result) < num_stock:
        stock_id = random.sample(stocks, 1)[0]
        end_date_margin = str(datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=invest_interval_map[f"{invest_interval}"]))
        real_data_start_date = date_margin.loc[date_margin["id"] == stock_id]["s"].values[0]
        real_data_end_date = date_margin.loc[date_margin["id"] == stock_id]["e"].values[0]
        if real_data_start_date<start_date and real_data_end_date>end_date_margin and stock_id not in list(result.keys()):
            print(stock_id)
            data = FetchData("stock", stock_id, key_path)
            result[f"{stock_id}"] = data
    return result

def GenerateAdjustDate(start_date, end_date, invest_interval):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    if invest_interval == "Month":
        adjust_date = pd.date_range(start=start_date, end=end_date, freq="MS").strftime("%Y-%m-%d").to_list()
    elif invest_interval == "Quarter":
        end_date = end_date + pd.offsets.MonthEnd(1) + timedelta(days=1)
        adjust_date = pd.date_range(start=start_date, end=end_date, freq="QS").strftime("%Y-%m-%d").to_list()
    elif invest_interval == "Year":
        adjust_date = pd.date_range(start=start_date, end=end_date, freq="YS").strftime("%Y-%m-%d").to_list()

    return adjust_date

def GetDataInterval(data, start_date, end_date):
    for key in list(data.keys()):
        full_data = data[f"{key}"]
        truncated_data = full_data.loc[(full_data["date"] >= start_date) & (full_data["date"] <= end_date)]
        data[f"{key}"] = truncated_data
    return data

def FindBuyPrice(df):
    for i in range(len(df)):
        if df.iloc[i]["open"] > 0:
            return df.iloc[i]['open']
    return 0.1

def FindSellPrice(df):
    for i in range(len(df)-1, 0, -1):
        if df.iloc[i]["open"] > 0:
            return df.iloc[i]['open']
    return 0.1

def ComputeProfit(data, balance):
    keys = list(data.keys())
    balance_for_each = balance // len(keys)
    buy_prices = np.array([FindBuyPrice(data[keys[i]]) for i in range(len(keys))])
    sell_prices = np.array([FindSellPrice(data[keys[i]]) for i in range(len(keys))])
    sell_prices[np.isnan(sell_prices)]=0
    profits_per_share = sell_prices-buy_prices
    profit_ratios = np.round((profits_per_share / np.array(buy_prices))*100, 2)
    shares = np.array([balance_for_each // buy_prices[i] for i in range(len(buy_prices))])
    new_balance = np.round(np.sum(profits_per_share*shares) + balance, 0)
    return new_balance, profit_ratios

def MonkeySelectStock(start_date, end_date, invest_interval, num_stock, category, balance, key_path):
    new_balances = [balance]
    profit_ratioss = []
    stockss = []
    balance_0050 = balance
    new_balances_0050 = [balance_0050]
    adjust_dates = GenerateAdjustDate(start_date, end_date, invest_interval)
    dates = [adjust_dates[0]]

    for i in range(len(adjust_dates)-1):
        full_data = GenerateRandomStockList(adjust_dates[i], num_stock, category, invest_interval, key_path)
        last_day = str(datetime.strptime(adjust_dates[i+1], "%Y-%m-%d")-timedelta(days=1))
        truncated_data = GetDataInterval(full_data, adjust_dates[i], last_day)

        full_data_0050 = FetchData("stock", "s0050", key_path)
        full_data_0050 = {"s0050" : full_data_0050}
        last_day = str(datetime.strptime(adjust_dates[i+1], "%Y-%m-%d")-timedelta(days=1))
        truncated_data_0050 = GetDataInterval(full_data_0050, adjust_dates[i], last_day)

        balance, profit_ratios = ComputeProfit(truncated_data, balance)
        balance_0050, _ = ComputeProfit(truncated_data_0050, balance_0050)

        new_balances.append(balance)
        new_balances_0050.append(balance_0050)

        profit_ratioss.append(profit_ratios)
        stockss.append([i[1:] for i in list(full_data.keys())])
        dates.append(adjust_dates[i+1])

    return new_balances, new_balances_0050, dates, profit_ratioss, stockss