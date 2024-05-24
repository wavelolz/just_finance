import pandas as pd
from google.cloud import firestore
import json
import mysql.connector
import os


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

def load_config(db_name):
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config_path = os.path.join(dir_path, "secret_info/config.json")
    with open(config_path, 'r') as file:
        config = json.load(file)

    if db_name == "raw":
        return config[0]
    elif db_name == "test":
        return config[1]
    
def GetConnection():
    config = load_config("test")
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
    query_data = f"select date, open, close from test.{stock_id}"
    cursor.execute(query_data)
    data = pd.DataFrame(cursor.fetchall())
    data.columns = ["date", "open", "close"]
    return data

stock_id = "s6863"
data = FetchData(stock_id)
data = data.set_index("date")
data = data.to_dict(orient="index")
data = json.loads(json.dumps(data))
upload_to_firestore(data, db, "stock", stock_id)

