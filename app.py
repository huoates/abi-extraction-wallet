import json
from datetime import datetime

import streamlit as st
from streamlit_local_storage import LocalStorage

# Initialize LocalStorage component
local_storage = LocalStorage()

st.set_page_config(page_title="Wallet Tracker", page_icon="💰")
st.title("ABI Extraction Wallet")

# 1. Initialize Transactions in Session State
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# 2. Sync from Local Storage on Load
# The component takes a moment to communicate with the browser.
# We wait until it returns a non-None value (even if it's an empty string).
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


# 3. Helper function to save changes
def save_to_storage():
    local_storage.setItem("transactions", json.dumps(st.session_state.transactions))


# 4. Calculation Logic
def calculate_total():
    total = 0
    for transaction in st.session_state.transactions:
        if transaction["action"] == "Add":
            total += transaction["amount"]
        elif transaction["action"] == "Subtract":
            total -= transaction["amount"]
    return total


# 5. UI: Metric Placeholder
# We reserve this space at the top so the total can be updated at the end of the script.
metric_placeholder = st.empty()

# 6. UI: Inputs (Positioned ABOVE the log)
amount = st.number_input("Enter amount:", min_value=0, value=0, step=1, format="%d")

col1, col2 = st.columns(2)

with col1:
    if st.button("Add", use_container_width=True):
        if amount > 0:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.transactions.append(
                {
                    "action": "Add",
                    "amount": amount,
                    "timestamp": timestamp,
                    "key": f"add_{timestamp}_{len(st.session_state.transactions)}",
                }
            )
            save_to_storage()
            st.toast(f"Added ${amount:,}", icon="✅")
            # We don't call st.rerun() here to ensure the success message stays visible
            # and the storage component has time to render its update.
        else:
            st.error("Amount must be greater than 0.")

with col2:
    if st.button("Subtract", use_container_width=True):
        if amount > 0:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.transactions.append(
                {
                    "action": "Subtract",
                    "amount": amount,
                    "timestamp": timestamp,
                    "key": f"sub_{timestamp}_{len(st.session_state.transactions)}",
                }
            )
            save_to_storage()
            st.toast(f"Subtracted ${amount:,}", icon="⚠️")
        else:
            st.error("Amount must be greater than 0.")

st.divider()

# 7. UI: Transaction Log (Positioned BELOW the inputs)
st.subheader("Transaction Log")

if st.session_state.transactions:
    # Sort transactions by timestamp (newest first)
    sorted_transactions = sorted(
        st.session_state.transactions, key=lambda x: x["timestamp"], reverse=True
    )

    for transaction in sorted_transactions:
        col_log, col_delete = st.columns([5, 1])
        with col_log:
            st.write(
                f"**{transaction['action']}** ${transaction['amount']:,}  \n_{transaction['timestamp']}_"
            )
        with col_delete:
            if st.button("Delete", key=f"del_{transaction['key']}"):
                # Filter out the transaction
                st.session_state.transactions = [
                    t
                    for t in st.session_state.transactions
                    if t["key"] != transaction["key"]
                ]
                save_to_storage()
                st.rerun()  # Rerun to refresh the list immediately
else:
    st.info("No transactions recorded yet.")

# 8. Final Update
# Update the metric at the very top with the current state (reflecting any additions/subtractions)
metric_placeholder.metric("Current Total", f"${calculate_total():,}")
