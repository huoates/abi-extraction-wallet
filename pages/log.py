import streamlit as st

import utils

st.set_page_config(page_title="Transaction Log", page_icon="📜")
st.title("Full Transaction History")

# 1. Sync from Local Storage on Load
utils.sync_from_storage()

# 2. Display Current Total
total = utils.calculate_total()
st.metric("Total Balance", f"${total:,}")

st.divider()

# 3. Full Transaction List
if st.session_state.get("transactions"):
    # Sort transactions by timestamp (newest first)
    sorted_transactions = sorted(
        st.session_state.transactions, key=lambda x: x["timestamp"], reverse=True
    )

    st.write(f"Showing all {len(sorted_transactions)} transactions.")

    for transaction in sorted_transactions:
        col_log, col_delete = st.columns([5, 1])
        with col_log:
            st.write(
                f"**{transaction['action']}** ${transaction['amount']:,}  \n_{transaction['timestamp']}_"
            )
        with col_delete:
            # Unique key for this page to avoid collisions with home page buttons
            if st.button("Delete", key=f"del_full_{transaction['key']}"):
                utils.delete_transaction(transaction["key"])
else:
    st.info("No transactions recorded yet. Go to the Home page to add some!")

# 4. Navigation helper
if st.button("← Back to Home"):
    st.switch_page("app.py")
