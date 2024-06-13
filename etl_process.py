from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from google.cloud import firestore

@st.cache_data
def FetchDatasetList(key_path):
    db = firestore.Client.from_service_account_json(key_path)
    doc_ref = db.collection("info").document("info_data")
    doc = doc_ref.get()
    data = doc.to_dict()
    df = pd.DataFrame.from_dict(data, orient="index")
    df.reset_index(inplace=True)
    df.rename(columns={"index" : "id"}, inplace=True)
    return df

@st.cache_data
def FetchData(collection_name, stock_id, key_path):
    db = firestore.Client.from_service_account_json(key_path)
    doc_ref = db.collection(collection_name).document(stock_id)
    doc = doc_ref.get()
    data = doc.to_dict()
    data = {k: data[k] for k in sorted(data)}
    df = pd.DataFrame.from_dict(data, orient="index")
    df.reset_index(inplace=True)
    df.rename(columns={"index" : "date"}, inplace=True)
    return df

@st.cache_data
def FetchChineseName(key_path):
    db = firestore.Client.from_service_account_json(key_path)
    doc_ref = db.collection("info").document("info_data")
    doc = doc_ref.get()
    data = doc.to_dict()
    data = {k: data[k] for k in sorted(data)}
    df = pd.DataFrame.from_dict(data, orient="index")
    df.reset_index(inplace=True)
    df.rename(columns={"index" : "id"}, inplace=True)
    l = [df.iloc[i]["id"][1:].upper()+"-"+df.iloc[i]["n"] for i in range(len(df))]
    return l

@st.cache_data
def FetchDateMargin(key_path):
    db = firestore.Client.from_service_account_json(key_path)
    doc_ref = db.collection("date_margin").document("date_margin_data")
    doc = doc_ref.get()
    data = doc.to_dict()
    df = pd.DataFrame.from_dict(data, orient="index")
    df.reset_index(inplace=True)
    df.rename(columns={"index" : "id"}, inplace=True)
    return df

@st.cache_data
def CleanData(data):
    filter_data = data.loc[data["close"] != 0]
    return filter_data

@st.cache_data
def ExtractMarketCloseDate(data):
    date_l = data["date"].to_list()
    start_date = datetime.strptime(date_l[0], "%Y-%m-%d")
    end_date = datetime.strptime(date_l[-1], "%Y-%m-%d")
    diff = (end_date-start_date).days
    all_days = [str(start_date+timedelta(days=i)).split(" ")[0] for i in range(diff)]
    close_days = sorted(set(all_days)-set(date_l))
    return close_days