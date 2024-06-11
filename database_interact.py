import pandas as pd
from google.cloud import firestore
import json
import mysql.connector
import os
import time


dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
key_path = os.path.join(dir_path, "secret_info/stockaroo-privatekey.json")
db = firestore.Client.from_service_account_json(key_path)

def upload_to_firestore(data, db, collection_name, doc_id):
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.set(data)

def delete_document(db, collection_name, doc_id):
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.delete()

def FetchDatasetList(collection_name):
    collection_ref = db.collection(collection_name)
    docs = collection_ref.stream()
    stock_ids = []
    for doc in docs:
        stock_ids.append(doc.id)
    return stock_ids

def load_config():
    config_path = "secret_info/config.json"
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config[0]

def GetConnection():
    config = load_config()
    db_connection = mysql.connector.connect(
    host=config["host"],
    user=config["user"],
    password=config["password"],
    database=config["database"]
    )
    return db_connection

def FetchData(stock_id):
    conn = GetConnection()
    cursor = conn.cursor()
    query_data = f"select date, open, close from stock.{stock_id}"
    cursor.execute(query_data)
    data = pd.DataFrame(cursor.fetchall())
    data.columns = ["date", "open", "close"]
    return data

def extract_table_name():
    config = load_config()

    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    query = """ 
            select TABLE_NAME as table_name
            from information_schema.tables
            where table_schema = 'stock';
            """
    cursor.execute(query)
    rows = cursor.fetchall()
    table_name = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])["table_name"].to_list()

    return table_name

def extract_table_name_excel(category):
    data = pd.read_excel("unique_stock_data_corrected.xlsx")
    data = data.loc[data["industry_category"] == f"{category}"]
    ids = data["stock_id"].to_list()
    return ids


# delete_document(db, "stock", "s2801")

stock_ids = extract_table_name_excel("金融保險")
stock_ids = ["s"+str(i) for i in stock_ids]

for id in stock_ids:
    try:
        data = FetchData(id)
        data = data.set_index("date")
        data = data.to_dict(orient="index")
        data = json.loads(json.dumps(data))
        upload_to_firestore(data, db, "stock", id)
        print(f"{id} has been uploaded")
        time.sleep(2)
    except:
        pass        

