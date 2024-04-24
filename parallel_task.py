import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import requests
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import mysql.connector

def read_token():
    with open("../secret_info/finmind_token.txt") as f:
        token = []
        for line in f.readlines():
            token.append(line)
    return token

def read_db_info():
    with open("../secret_info/mysql_password.txt") as f:
        for line in f.readlines():
            password = line
    return password

def create_stock_id_list():
    stock_id = pd.read_csv("stock_id.csv")["stock_id"][:60].to_list()
    n = len(stock_id)
    size = n // 6 + (1 if n % 6 > 0 else 0)
    stock_id_sublist = [stock_id[i:i+size] for i in range(0, n, size)]
    return stock_id_sublist

def fetch_data(token, stock_id, date):
    print(f"Currently Fetching: {stock_id}")
    start_date = str(datetime.strptime(date, "%Y-%m-%d")-timedelta(days=5)).split(" ")[0]
    end_date = str(datetime.strptime(date, "%Y-%m-%d")+timedelta(days=2)).split(" ")[0]
    parameter = {
        "dataset": "TaiwanStockPrice",
        "data_id": f"{stock_id}",
        "start_date": f"{start_date}",
        "end_date": f"{end_date}",
        "token": f"{token}"
    }
    url = "https://api.finmindtrade.com/api/v4/data"
    resp = requests.get(url, params=parameter)
    data = resp.json()
    try:
        data = pd.DataFrame(data["data"])
    except:
        print(data)
        print(token)
    return data

def manage_token(token, stock_list, date):
    result = []
    for stock_id in stock_list:
        result.append(fetch_data(token, stock_id, date))
    return result

def fetch_all_data(date):
    stock_list = create_stock_id_list()
    token = read_token()
    token = [i.strip() for i in token]
    token = [i for i in token if len(i)>0]
    result = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(manage_token, token[i], stock_list[i], date) for i in range(len(token))]
        for future in as_completed(futures):
            result.extend(future.result())
    end = time.time()
    print(f"Time Spent: {np.round(end-start)}")
    return result

def clear_invalid_data(stock_df_list):
    result = []
    for stock_df in stock_df_list:
        if len(stock_df)>0:
            result.append(stock_df)
    return result

def load_to_db(stock_df_list):
    engine_path = read_db_info()
    engine = create_engine(f"{engine_path}")
    for stock_df in stock_df_list:
        name = stock_df.iloc[0]['stock_id']
        stock_df.to_sql(name=f"s{name}", con=engine, if_exists="replace", index=False)
        print(f"{name} loaded successfully")
        time.sleep(1)

def filter_date(stock_df_list, date):
    result = []
    for stock_df in stock_df_list:
        filter_df = stock_df.loc[stock_df["date"].isin([date])]
        result.append(filter_df)
    return result

def load_new_row_to_db(stock_df_list):
    engine_path = read_db_info()
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
        "token": f"{token[0]}"
    }
    url = "https://api.finmindtrade.com/api/v4/data"
    resp = requests.get(url, params=parameter)
    data = resp.json()
    data = pd.DataFrame(data["data"])
    print(data)
    filter_df = data.loc[data["date"].isin([date])]
    if len(filter_df)>0:
        return True
    else:
        return False

def read_data():
    config = {
        "user" : "root",
        "password" : "@Fk10150305msds",
        "host" : "127.0.0.1",
        "database" : "test"
    }

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

if __name__ == "__main__":
    read_data()
    # date = testing_get_date()
    # print(f"Today is {date}")
    # print(check_trading_or_not(date))
    # result = fetch_all_data("2020-0101")
    # result = clear_invalid_data(result)
    # load_to_db(result)
    # result = filter_date(result, date)
    # load_new_row_to_db(result)

