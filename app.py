from datetime import datetime

import streamlit as st

import wallet_utils

st.set_page_config(page_title="Wallet Tracker", page_icon="💰")

# Custom CSS to change the cursor to a pointer for the selectbox
st.markdown(
    """
    <style>
    div[data-baseweb="select"], div[data-baseweb="select"] * {
        cursor: pointer !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("ABI Extraction Wallet")

# 1. Sync from Local Storage on Load
wallet_utils.sync_from_storage()

# 2. UI: Metric Placeholder
metric_placeholder = st.empty()

# 3. UI: Inputs
zone = st.selectbox(
    "Zone:",
    options=["TV Station", "Airport", "Armory", "Farm", "Valley", "Northridge"],
    index=0,
)

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
                    "zone": zone,
                    "timestamp": timestamp,
                    "key": f"add_{timestamp}_{len(st.session_state.transactions)}",
                }
            )
            wallet_utils.save_to_storage()
            st.toast(f"Added ${amount:,}", icon="✅")
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
                    "zone": zone,
                    "timestamp": timestamp,
                    "key": f"sub_{timestamp}_{len(st.session_state.transactions)}",
                }
            )
            wallet_utils.save_to_storage()
            st.toast(f"Subtracted ${amount:,}", icon="⚠️")
        else:
            st.error("Amount must be greater than 0.")

st.divider()

# 4. UI: Transaction Log (Recent 5)
st.subheader("Recent Transactions")

if st.session_state.get("transactions"):
    # Sort transactions by timestamp (newest first) and take top 5
    sorted_transactions = sorted(
        st.session_state.transactions, key=lambda x: x["timestamp"], reverse=True
    )
    recent_transactions = sorted_transactions[:5]

    for transaction in recent_transactions:
        col_log, col_delete = st.columns([5, 1])
        with col_log:
            zone_info = (
                f" | {transaction.get('zone', 'N/A')}" if "zone" in transaction else ""
            )
            st.write(
                f"**{transaction['action']}** ${transaction['amount']:,}{zone_info}  \n_{transaction['timestamp']}_"
            )
        with col_delete:
            if st.button("Delete", key=f"del_home_{transaction['key']}"):
                wallet_utils.delete_transaction(transaction["key"])

    if len(st.session_state.transactions) > 5:
        st.info(f"Showing 5 of {len(st.session_state.transactions)} transactions.")
        if st.button("View All Transactions"):
            st.switch_page("pages/log.py")
else:
    st.info("No transactions recorded yet.")

# 5. Final Update
metric_placeholder.metric("Current Total", f"${wallet_utils.calculate_total():,}")
