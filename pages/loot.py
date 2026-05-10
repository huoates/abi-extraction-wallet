import pandas as pd
import streamlit as st
from st_supabase_connection import SupabaseConnection

conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"],
)

response = conn.table("openings_by_container").select("*").execute()
df = pd.DataFrame(response.data)
# df["count"] = pd.to_numeric(df["count"])
df = df.sort_values(by="count", ascending=False)
st.write(df)
st.title("Openings by Container")
st.bar_chart(df, x="name", y="count")

response = conn.table("koen_per_container_open").select("*").execute()
df_koen = pd.DataFrame(response.data)
df_koen = df_koen.sort_values(by="avg_koen_per_open", ascending=False)
st.title("Koen per Container Open")
st.bar_chart(df_koen, x="name", y="avg_koen_per_open")

st.title("Koen Per Slot Per Open by Container")
st.bar_chart(df_koen, x="name", y="avg_koen_per_slot_per_open")
