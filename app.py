import streamlit as st
from st_supabase_connection import SupabaseConnection

conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"],
)

if "code" in st.query_params:
    auth_code = st.query_params["code"]
    try:
        conn.client.auth.exchange_code_for_session(
            {"auth_code": auth_code}
        )  # type: ignore
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Authentication failed: {e}")

session = None
try:
    session = conn.client.auth.get_session()
except Exception:
    pass

home = st.Page("pages/home.py", title="Home", icon="🏠")
wallet = st.Page("pages/wallet.py", title="Wallet", icon="💼")
log = st.Page("pages/log.py", title="Wallet Transactions", icon="📜")
loot_tracker = st.Page("pages/loot_tracker.py", title="Loot Tracker", icon="📜")
loot = st.Page("pages/loot.py", title="Loot")
demo = st.Page("pages/demo.py", title="Demo")
add_item_image = st.Page("pages/add_item_image.py", title="Add Item Image", icon="🖼️")
ai_add_loot = st.Page("pages/ai_add_loot.py", title="AI Add Loot", icon="🖼️")
loot_review = st.Page("pages/loot_review.py", title="Loot Review", icon="🔍")

pg = st.navigation(
    [
        home,
        wallet,
        log,
        loot_tracker,
        loot,
        demo,
        add_item_image,
        ai_add_loot,
        loot_review,
    ]
)


if session:
    user = session.user
    with st.sidebar:
        st.write(f"Welcome, {user.email}!")
        if st.button("Log Out", use_container_width=True):
            conn.client.auth.sign_out()
            st.rerun()
    pg.run()

else:
    with st.sidebar:
        response = conn.client.auth.sign_in_with_oauth(
            {
                "provider": "discord",
                "options": {"redirect_to": "http://localhost:8501"},
            }
        )
        st.link_button(
            "Login with Discord",
            response.url if response.url else "",
            use_container_width=True,
        )
