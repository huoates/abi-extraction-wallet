import json

import streamlit as st
from streamlit_local_storage import LocalStorage

# Initialize LocalStorage component
local_storage = LocalStorage()


def sync_from_storage():
    """Sync transactions from local storage to session state."""
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

    if "storage_synced" not in st.session_state:
        stored_data = local_storage.getItem("transactions")
        if stored_data is not None:
            if stored_data:
                try:
                    st.session_state.transactions = json.loads(stored_data)
                except Exception:
                    pass
            st.session_state.storage_synced = True
            st.rerun()


def save_to_storage():
    """Save the current session state transactions to local storage."""
    local_storage.setItem("transactions", json.dumps(st.session_state.transactions))


def calculate_total():
    """Calculate the total balance from transactions."""
    total = 0
    for transaction in st.session_state.transactions:
        if transaction["action"] == "Add":
            total += transaction["amount"]
        elif transaction["action"] == "Subtract":
            total -= transaction["amount"]
    return total


def delete_transaction(transaction_key):
    """Delete a transaction by its key and persist the change."""
    st.session_state.transactions = [
        t for t in st.session_state.transactions if t["key"] != transaction_key
    ]
    save_to_storage()
    st.rerun()
