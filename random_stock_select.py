from etl_process import FetchDatasetList, FetchData, FetchDateMargin
from datetime import datetime, timedelta
import random
import numpy as np
import os
import pandas as pd


def GenerateRandomStockList(start_date, num_stock, category, invest_interval, key_path):
    result = {}
    if invest_interval == "年":
        invest_interval = "Year"

    stock_df = FetchDatasetList(key_path)

    category_map = {
        "Semiconductor Industry": "半導體業",
        "Automotive Industry": "汽車工業",
        "Electronic Components Industry": "電子零組件業",
        "Glass and Ceramics": "玻璃陶瓷",
        "ETN": "ETN",
        "Digital Cloud": "數位雲端",
        "Biotechnology and Medical Care": "生技醫療",
        "Building Materials and Construction": "建材營造",
        "Rubber Industry": "橡膠工業",
        "Other Electronics": "其他電子類",
        "Electronics Industry": "電子工業",
        "Beneficiary Securities": "受益證券",
        "Steel Industry": "鋼鐵工業",
        "Computer and Peripheral Equipment Industry": "電腦及週邊設備業",
        "Food Industry": "食品工業",
        "Green Energy and Environmental Protection": "綠能環保",
        "Depositary Receipts": "存託憑證",
        "Innovative Board Stocks": "創新版股票",
        "Oil, Electricity, and Gas Industry": "油電燃氣業",
        "Cement Industry": "水泥工業",
        "Optoelectronics Industry": "光電業",
        "Agricultural Technology": "農業科技",
        "Cultural and Creative Industry": "文化創意業",
        "Tourism Industry": "觀光事業",
        "Telecommunication and Network Industry": "通信網路業",
        "Others": "其他",
        "Shipping Industry": "航運業",
        "Paper Industry": "造紙工業",
        "Finance and Insurance": "金融保險",
        "Tourism and Hospitality": "觀光餐旅",
        "Textile and Fiber": "紡織纖維",
        "Electrical Appliances and Cables": "電器電纜",
        "Electrical Machinery": "電機機械",
        "Home and Living": "居家生活",
        "Trading and Department Stores": "貿易百貨",
        "Electronic Distribution Industry": "電子通路業",
        "Information Service Industry": "資訊服務業",
        "Chemical Industry": "化學工業",
        "Plastics Industry": "塑膠工業",
        "ETF": "ETF"
}

    if category in category_map.keys():
        category = category_map[category]
        
    if category == "All" or category == "全部":
        stocks = stock_df["id"].to_list()
    else:
        stocks = stock_df.loc[stock_df["c"] == category]["id"].to_list()

    date_margin = FetchDateMargin(key_path)
    while len(result) < num_stock:
        stock_id = random.sample(stocks, 1)[0]
        end_date_margin = str(datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=380))
        real_data_start_date = date_margin.loc[date_margin["id"] == stock_id]["s"].values[0]
        real_data_end_date = date_margin.loc[date_margin["id"] == stock_id]["e"].values[0]
        if real_data_start_date<start_date and real_data_end_date>end_date_margin and stock_id not in list(result.keys()):
            data = FetchData("stock", stock_id, key_path)
            result[f"{stock_id}"] = data
    return result

def GenerateAdjustDate(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
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
        if df.iloc[i]["o"] > 0:
            return df.iloc[i]['o']
    return 0.1

def FindSellPrice(df):
    for i in range(len(df)-1, 0, -1):
        if df.iloc[i]["o"] > 0:
            return df.iloc[i]['o']
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

def MonkeySelectStock(start_date, end_date, num_stock, category, balance, key_path, progress_callback=None, invest_interval=None):
    _ = None
    new_balances = [balance]
    profit_ratioss = []
    stockss = []
    balance_0050 = balance
    new_balances_0050 = [balance_0050]
    adjust_dates = GenerateAdjustDate(start_date, end_date)
    dates = [adjust_dates[0]]
    total_steps = len(adjust_dates)-1

    for i in range(total_steps):
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

        if progress_callback:
            progress_callback(i + 1, total_steps)

    return new_balances, new_balances_0050, dates, profit_ratioss, stockss
