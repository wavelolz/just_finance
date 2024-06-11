#%%
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import requests
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import mysql.connector
import json
import os
from proxy_requests.proxy_requests import ProxyRequests

def read_token():
    with open("secret_info/finmind_token.txt") as f:
        token = f.readline()
    return token

def read_db_info(mode):
    info = []
    mysql_info_path = "secret_info/mysql_connect_info.txt"
    with open(mysql_info_path) as f:
        for line in f.readlines():
            info.append(line)
    if mode == "ext":
        return info[0]
    elif mode == "load":
        return info[1]

def fetch_data(token, stock_id, start_date, end_date):
    print(f"Currently Fetching: {stock_id}")
    parameter = {
        "dataset": "TaiwanStockPrice",
        "data_id": f"{stock_id}",
        "start_date": f"{start_date}",
        "end_date": f"{end_date}",
        "token": f"{token}"
    }
    url = "https://api.finmindtrade.com/api/v4/data"
    resp = requests.get(url, parameter)
    data = resp.json()
    status = data["status"]
    data = pd.DataFrame(data["data"])
    data = data[["date", "open", "close"]]
    
    return data, status

def manage_token(token, stock_list, start_date, end_date):
    result = []
    for stock_id in stock_list:
        while True:
            try:
                data, status = fetch_data(token, stock_id, start_date, end_date)
                if int(status) != 402:
                    stock_data_dict = {f"{stock_id}" : data}
                    result.append(stock_data_dict)
                    time.sleep(6.1)
                    break
                else:
                    print("Upper Limit reached, resting...")
                    time.sleep(1800)
            except KeyError:
                print(f"Invalid stock data: {stock_id}")
                break
            except ConnectionAbortedError:
                print("Encountering connection error, press Enter to continue")
                input()
            except ConnectionError:
                print("Encountering connection error, press Enter to continue")
                input()


    return result

def fetch_all_data(start_date, end_date):
    stock_list = pd.read_excel("unique_stock_data_corrected.xlsx")["stock_id"].to_list()[2000:]
    token = read_token()
    result = manage_token(token, stock_list, start_date, end_date)
    return result

def clear_invalid_data(stock_df_list):
    result = []
    for stock_df in stock_df_list:
        if len(stock_df)>0:
            result.append(stock_df)
    return result

def load_to_db(stock_df_list, mode):
    engine_path = read_db_info(mode)
    engine = create_engine(f"{engine_path}")
    for stock_df in stock_df_list:
        for key, val in stock_df.items():
            val.to_sql(name=f"s{key}", con=engine, if_exists="replace", index=False)
            print(f"{key} loaded successfully")
            time.sleep(1)

def filter_date(stock_df_list, date):
    result = []
    for stock_df in stock_df_list:
        filter_df = stock_df.loc[stock_df["date"].isin([date])]
        result.append(filter_df)
    return result

def load_new_row_to_db(stock_df_list, mode):
    engine_path = read_db_info(mode)
    engine = create_engine(f"{engine_path}")
    for stock_row in stock_df_list:
        name = stock_row.iloc[0]["stock_id"]
        stock_row.to_sql(name=f"s{name}", con=engine, if_exists="append", index=False)
        print(f"{name} inserted successfully")
        time.sleep(1)

def testing_get_date():
    with open("current_date.txt") as f:
        for line in f.readlines():
            date = line
    current_date = date
    new_date = str(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1))
    new_date = new_date.split(" ")[0]
    with open("current_date.txt", "w") as f:
        f.write(new_date)
    return current_date

def check_trading_or_not(date):
    start_date = str(datetime.strptime(date, "%Y-%m-%d")-timedelta(days=5)).split(" ")[0]
    end_date = str(datetime.strptime(date, "%Y-%m-%d")+timedelta(days=2)).split(" ")[0]
    token = read_token()
    parameter = {
        "dataset": "TaiwanStockPrice",
        "data_id": f"2330",
        "start_date": f"{start_date}",
        "end_date": f"{end_date}",
        # "token": f"{token[0]}"
        "token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMyAxMzo1OTo1MyIsInVzZXJfaWQiOiJ3YXZlbG9sejYiLCJpcCI6IjExMS4yNDIuMTg4LjE5NCJ9.Yt851qpXU_wTmhiYIbQec6nm4Vf8wdhY4mFqUWA6Llg"
    }
    url = "https://api.finmindtrade.com/api/v4/data"
    resp = requests.get(url, params=parameter)
    data = resp.json()
    # data = pd.DataFrame(data["data"])
    print(data)
    filter_df = data.loc[data["date"].isin([date])]
    if len(filter_df)>0:
        return True
    else:
        return False

def load_config(db_name):
    filename = "../secret_info/config.json"
    with open(filename, 'r') as file:
        config = json.load(file)

    if db_name == "raw":
        return config[0]
    elif db_name == "test":
        return config[1]

def read_data():
    config = load_config("raw")

    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    query = """ 
            select TABLE_NAME as table_name
            from information_schema.tables
            where table_schema = 'test';
            """
    cursor.execute(query)
    rows = cursor.fetchall()
    table_name = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])["table_name"].to_list()

    result = []
    for i in table_name:
        query = f"select * from {i}"
        cursor.execute(query)
        rows = cursor.fetchall()
        data = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        result.append(data)

    cursor.close()
    cnx.close()
    return result
#%%
result1 = fetch_all_data("2011-01-01", "2024-05-01")

#%%
result2 = fetch_all_data("2011-01-01", "2024-05-01")

#%%
result3 = fetch_all_data("2011-01-01", "2024-05-01")

#%%
result4 = fetch_all_data("2011-01-01", "2024-05-01")
#%%
result4 = clear_invalid_data(result4)
load_to_db(result4, "ext")
