from etl_process import FetchDatasetList, FetchData
from datetime import datetime, timedelta
import random
import numpy as np
import os


def GenerateRandomStockList(start_date, num_stock, key_path):
    result = {}
    while len(result) < num_stock:
        stock_id = random.sample(FetchDatasetList("stock", key_path), 1)[0]
        data = FetchData("stock", stock_id, key_path)
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
        if df.iloc[i]["open"] > 0:
            return df.iloc[i]['open']
    return np.NAN

def FindSellPrice(df):
    for i in range(len(df)-1, 0, -1):
        if df.iloc[i]["open"] > 0:
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
    new_balance = np.round(np.sum(profits_per_share*shares) + balance, 0)
    return new_balance, profit_ratios

def MonkeySelectStock(start_date, end_date, num_stock, balance, key_path):
    new_balances = [balance]
    dates = [start_date]
    profit_ratioss = []
    stockss = []
    balance_0050 = balance
    new_balances_0050 = [balance_0050]
    while str(start_date) <= end_date:
        full_data = GenerateRandomStockList(str(start_date).split(" ")[0], num_stock, key_path)
        truncated_data = GetDataInterval(full_data, str(start_date).split(" ")[0])

        full_data_0050 = FetchData("stock", "s0050", key_path)
        full_data_0050 = {"s0050" : full_data_0050}
        truncated_data_0050 = GetDataInterval(full_data_0050, str(start_date).split(" ")[0])

        balance, profit_ratios = ComputeProfit(truncated_data, balance)
        balance_0050, _ = ComputeProfit(truncated_data_0050, balance_0050)

        new_balances.append(balance)
        new_balances_0050.append(balance_0050)

        profit_ratioss.append(profit_ratios)
        stockss.append(list(full_data.keys()))
        start_date += timedelta(days=30)
        dates.append(start_date)
    return new_balances, new_balances_0050, dates, profit_ratioss, stockss