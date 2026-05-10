import streamlit as st
from st_supabase_connection import SupabaseConnection

from models import Container, Difficulty, Item, Opening, Zone

conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"],
)


def get_zones():
    response = conn.table("zone").select("id, name").execute()
    return [Zone.model_validate(zone) for zone in response.data]


def get_difficulties():
    response = conn.table("difficulty").select("id, name").execute()
    return [Difficulty.model_validate(difficulty) for difficulty in response.data]


def get_containers():
    response = conn.table("container").select("id, name").order("name").execute()
    return [Container.model_validate(container) for container in response.data]


def get_items():
    response = conn.table("item").select("id, name").order("name").execute()
    return [Item.model_validate(item) for item in response.data]


with st.form("item_form"):
    st.title("Add New Loot")

    selected_zone = st.selectbox(
        "Select a zone", get_zones(), format_func=lambda x: x.name
    )

    selected_difficulty = st.selectbox(
        "Select a difficulty", get_difficulties(), format_func=lambda x: x.name
    )

    selected_container = st.selectbox(
        "Select a container", get_containers(), format_func=lambda x: x.name
    )

    selected_items = st.multiselect(
        "Select an item", get_items(), format_func=lambda x: x.name
    )

    submit_button = st.form_submit_button("Submit")

if submit_button:
    if selected_zone and selected_difficulty and selected_container and selected_items:
        try:
            new_opening = {
                "zone_id": selected_zone.id,
                "difficulty_id": selected_difficulty.id,
                "container_id": selected_container.id,
            }
            response = conn.table("opening").insert(new_opening).execute()
            opening = Opening.model_validate(response.data[0])

            for item in selected_items:
                new_loot = {"item_id": item.id, "opening_id": opening.id}
                response = conn.table("loot").insert(new_loot).execute()
                if len(response.data) > 0:
                    st.success(f"Inserted entry: {response.data[0]}")
                    st.json(response.data)

        except Exception as e:
            st.error(f"Failed to insert entry: {e}")
    else:
        st.error("Please select all fields before submitting.")
