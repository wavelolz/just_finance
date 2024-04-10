import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import requests
import pandas as pd
from sqlalchemy import create_engine

def create_stock_id_list():
    stock_id = pd.read_csv("stock_id.csv")["stock_id"][:60].to_list()
    n = len(stock_id)
    size = n // 6 + (1 if n % 6 > 0 else 0)
    stock_id_sublist = [stock_id[i:i+size] for i in range(0, n, size)]
    return stock_id_sublist

def fetch_data(token, stock_id):
    print(stock_id)
    parameter = {
        "dataset": "TaiwanStockPrice",
        "data_id": f"{stock_id}",
        "start_date": "2022-01-01",
        "end_date": "2022-01-05",
        "token": f"{token}"
    }
    url = "https://api.finmindtrade.com/api/v4/data"
    resp = requests.get(url, params=parameter)
    data = resp.json()
    data = pd.DataFrame(data["data"])
    return data

def manage_token(token, stock_list):
    result = []
    for stock_id in stock_list:
        result.append(fetch_data(token, stock_id))
    return result

def fetch_all_data():
    stock_list = create_stock_id_list()
    token = [
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMyAxMzo1OTo1MyIsInVzZXJfaWQiOiJ3YXZlbG9sejYiLCJpcCI6IjExMS4yNDIuMTg4LjE5NCJ9.Yt851qpXU_wTmhiYIbQec6nm4Vf8wdhY4mFqUWA6Llg",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMyAxNDowMDo1MSIsInVzZXJfaWQiOiJ3YXZlbG9seiIsImlwIjoiMTExLjI0Mi4xODguMTk0In0.eSwJdtYXblwqttwVHBjOFhTFxfF6PuQYCLBTDal8Zb8",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMyAxNDowMToxNCIsInVzZXJfaWQiOiJ3YXZlbG9sejIiLCJpcCI6IjExMS4yNDIuMTg4LjE5NCJ9.XX7RRR7A4wuCGOAYe89UBJVuRSlMyBPkupEmdDxjF-c",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMyAxNDowMTozMiIsInVzZXJfaWQiOiJ3YXZlbG9sejMiLCJpcCI6IjExMS4yNDIuMTg4LjE5NCJ9.Y8ak_3e3af0bCGaGLOeHPGNn1_3qqr-xILWJ9gHH17c",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMyAxNDowMTo0NSIsInVzZXJfaWQiOiJ3YXZlbG9sejQiLCJpcCI6IjExMS4yNDIuMTg4LjE5NCJ9.3svTtIR6mdI8rwKTFwxJ7Fb5xAMgxxI17UyYAM7oz0k",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMyAxNDowMjoxMCIsInVzZXJfaWQiOiJ3YXZlbG9sejUiLCJpcCI6IjExMS4yNDIuMTg4LjE5NCJ9.CWZgKADe3TvlKFxlVR0IbLDOMBYegsqnMk1bkXAEZvQ"
    ]
    result = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(manage_token, token[i], stock_list[i]) for i in range(len(token))]
        for future in as_completed(futures):
            result.extend(future.result())
    end = time.time()
    print(end-start)
    print(result)
    return result

def clear_invalid_data(stock_df_list):
    result = []
    for stock_df in stock_df_list:
        if len(stock_df)>0:
            result.append(stock_df)
    return result

def load_to_db(stock_df_list):
    engine = create_engine("mysql+mysqlconnector://root:%40Fk10150305msds@127.0.0.1/test")
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
    engine = create_engine("mysql+mysqlconnector://root:%40Fk10150305msds@127.0.0.1/test")
    for stock_row in stock_df_list:
        name = stock_row.iloc[0]["stock_id"]
        stock_row.to_sql(name=f"s{name}", con=engine, if_exists="append", index=False)
        print(f"{name} inserted successfully")
        time.sleep(1)



if __name__ == "__main__":
    result = fetch_all_data()
    result = clear_invalid_data(result)
    print(result)
    # load_to_db(result)
    # result = filter_date(result, "2022-01-05")
    # load_new_row_to_db(result)

