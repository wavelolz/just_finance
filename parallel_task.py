import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import requests
import pandas as pd

def fetch_data(token, stock_id):
    print(stock_id)
    parameter = {
        "dataset": "TaiwanStockPrice",
        "data_id": f"{stock_id}",
        "start_date": "2020-04-02",
        "end_date": "2024-01-11",
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
    stock_list = [
        ["0050", "2330", "8033", "8201", "1609", "8147"],
        ["006208", "2464", "6210", "8996", "8092", "1616"],
        ["3708", "6189", "6517", "3294", "3597", "3058"]
    ]
    token = [
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMiAyMjoxNToyMCIsInVzZXJfaWQiOiJ3YXZlbG9seiIsImlwIjoiMTExLjI0Mi4yMTAuMjQ3In0.s-AWywsa2NxbONzZMyFM0Kz4CPBQ_NO5iNe83WdUZtc",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMiAyMjoxNTo0OSIsInVzZXJfaWQiOiJ3YXZlbG9sejMiLCJpcCI6IjExMS4yNDIuMjEwLjI0NyJ9.SERy9TByGEo0Qgy2NhXkJp6-lEA9Fh33cphYDQsgJ7A",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0yMiAyMjoxNjozMyIsInVzZXJfaWQiOiJ3YXZlbG9sejQiLCJpcCI6IjExMS4yNDIuMjEwLjI0NyJ9.bkm9aizC3C9HEtgQlNU9PxjkVCjyTTccbBcPxDVbmvQ"
    ]
    input_arg = zip(token, stock_list)
    result = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(manage_token, token[i], stock_list[i]) for i in range(len(token))]
        for future in as_completed(futures):
            result.extend(future.result())
    end = time.time()
    print(end-start)
    print(result)


if __name__ == "__main__":
    fetch_all_data()

