#%%
from FinMind.data import DataLoader
import ta
from ta import add_all_ta_features
from ta.utils import dropna
import pandas as pd
import time
#%%

dl = DataLoader()
# 下載台股股價資料
stock_data = dl.taiwan_stock_daily(
    stock_id='0061', start_date='2023-01-01', end_date='2024-03-01'
)

print(stock_data)

#%%
stock_data = dropna(stock_data)
df = add_all_ta_features(stock_data, open="open", close="close", low="min", high="max", volume="Trading_Volume")

#%%
rsi = ta.momentum.RSIIndicator(stock_data["close"], 14)
print(stock_data["close"][-10:])
print(rsi.rsi()[-10:])

#%%
print(stock_data.iloc[-10:])

#%%
import mysql.connector
db_connection = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  password="@Fk10150305msds",
  database="test"
)

#%%
cursor = db_connection.cursor()

# Example SQL query to insert data
query = "INSERT INTO first_table (col1, col2) VALUES (%s, %s)"
values = ("value1", "value2")

cursor.execute(query, values)

# Commit the transaction
db_connection.commit()

print(cursor.rowcount, "record inserted.")

#%%
cursor.close()
db_connection.close()

#%%

from sqlalchemy import create_engine
engine = create_engine("mysql+mysqlconnector://root:%40Fk10150305msds@127.0.0.1/test")


#%%
import requests
url = "https://api.finmindtrade.com/api/v4/login"
payload = {
    "user_id" : "rayhsu005@gmail.com",
    "password" : "FK10150305"
}
data = requests.post(url, data=payload)
data = data.json()
#%%
url = "https://api.finmindtrade.com/api/v4/data"
parameter = {
    "dataset": "TaiwanStockInfo",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0wNSAxOToyMTo1MyIsInVzZXJfaWQiOiJ3YXZlbG9seiIsImlwIjoiMTExLjI0Mi4yMjguMTIzIn0.gzyLIR7JDgpEa4QCJEseznuaL6HMM3tepZPAzZgxAAE"
}
resp = requests.get(url, params=parameter)
stock_data = pd.DataFrame(resp.json()["data"])
stock_id = stock_data["stock_id"].to_list()[:200]
#%%
url = "https://api.finmindtrade.com/api/v4/data"
def GetData(stock_id):
  parameter = {
      "dataset": "TaiwanStockPrice",
      "data_id": f"{stock_id}",
      "start_date": "2020-04-02",
      "end_date": "2024-01-11",
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0wNSAxOToyMTo1MyIsInVzZXJfaWQiOiJ3YXZlbG9seiIsImlwIjoiMTExLjI0Mi4yMjguMTIzIn0.gzyLIR7JDgpEa4QCJEseznuaL6HMM3tepZPAzZgxAAE"
  }
  resp = requests.get(url, params=parameter)
  data = resp.json()
  data = pd.DataFrame(data["data"])
  return data

for i in stock_id:
  data = GetData(i)
  if len(data) > 0:
    data.to_sql(name=f"s{i}", con=engine, if_exists="replace", index=False)
    print(f"Data {i} inserted")
  else:
    pass
  time.sleep(5)

#%%
url = "https://api.web.finmindtrade.com/v2/user_info"
payload = {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRlIjoiMjAyNC0wMy0wNSAxOToyMTo1MyIsInVzZXJfaWQiOiJ3YXZlbG9seiIsImlwIjoiMTExLjI0Mi4yMjguMTIzIn0.gzyLIR7JDgpEa4QCJEseznuaL6HMM3tepZPAzZgxAAE"
}
resp = requests.get(url, params=payload)
print(resp.json()["user_count"])  # 使用次數
print(resp.json()["api_request_limit"])  # api 使用上限