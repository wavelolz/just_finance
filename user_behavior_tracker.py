from google.cloud import firestore
from datetime import datetime
from google.oauth2 import service_account

# Function to save user session to Firestore
def save_user_session(user_id, key_path):
    credentials = service_account.Credentials.from_service_account_info(key_path)
    db = firestore.Client(credentials=credentials)
    user_ref = db.collection("users_testing").document(user_id)
    if not user_ref.get().exists:
        user_ref.set({
            "user_id": user_id,
            "created_at": datetime.now(),
            "tab1_click_count": 0,
            "tab2_click_count": 0,
            "tab3_click_count": 0
        })

def save_tab_click_counter(user_id, tab_name, count, key_path):
    credentials = service_account.Credentials.from_service_account_info(key_path)
    db = firestore.Client(credentials=credentials)
    user_ref = db.collection("users_testing").document(user_id)
    user_ref.update({
        tab_name: count,
        "timestamp": datetime.now()
    })
