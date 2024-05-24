import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from dotenv import load_dotenv

# Load Firebase configuration from .env file
load_dotenv()

# Load Firebase configuration from environment variables
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
FIREBASE_MESSAGING_SENDER_ID = os.getenv('FIREBASE_MESSAGING_SENDER_ID')
FIREBASE_APP_ID = os.getenv('FIREBASE_APP_ID')

# Path to your service account key JSON file
SERVICE_ACCOUNT_KEY_PATH = r"buttonclick-1982f.json"

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Initialize the counter in session state if it does not exist
if 'button_click_count' not in st.session_state:
    print("Yes")
    st.session_state["button_click_count"] = 0

# Function to increment the counter
def increment_counter():
    st.session_state.button_click_count += 1
    save_counter()

# Function to save the counter to Firebase Firestore
def save_counter():
    doc_ref = db.collection("button_clicks").document("click_count")
    doc_ref.set({
        "count": st.session_state.button_click_count,
        "timestamp": datetime.now()
    })

# Display the button and associate it with the increment function
if st.button('Click me!'):
    increment_counter()

# Display the current count
st.write(f"Button clicked {st.session_state.button_click_count} times.")
