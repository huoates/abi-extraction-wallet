import pandas as pd
import streamlit as st
from st_supabase_connection import SupabaseConnection

conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"],
)

response = conn.table("koen_efficiency_by_container").select("*").execute()
df_koen = pd.DataFrame(response.data)
df_koen = df_koen.sort_values(by="eligible_koen_per_slot_per_opening", ascending=False)
st.title("Average Koen per Slot per Opening by Container")
st.write("This visual assumes you only pick up items worth at least $5000 per slot.")
st.bar_chart(df_koen, x="container_name", y="eligible_koen_per_slot_per_opening")

response = conn.table("openings_by_container").select("*").execute()
df = pd.DataFrame(response.data)
df = df.sort_values(by="count", ascending=False)
st.write(df)
st.title("Openings by Container")
st.bar_chart(df, x="name", y="count")
