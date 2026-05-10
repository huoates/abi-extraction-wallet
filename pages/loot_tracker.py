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


def process_submission():
    if (
        st.session_state.selected_zone
        and st.session_state.selected_difficulty
        and st.session_state.selected_container
        and st.session_state.selected_items
    ):
        try:
            new_opening = {
                "zone_id": st.session_state.selected_zone.id,
                "difficulty_id": st.session_state.selected_difficulty.id,
                "container_id": st.session_state.selected_container.id,
            }
            response = conn.table("opening").insert(new_opening).execute()
            opening = Opening.model_validate(response.data[0])

            for item in st.session_state.selected_items:
                new_loot = {"item_id": item.id, "opening_id": opening.id}
                response = conn.table("loot").insert(new_loot).execute()
                if len(response.data) > 0:
                    st.session_state.status_type = "success"
                    st.session_state.status_msg = f"Inserted entry: {response.data[0]}"
                    st.session_state.response_json = response.data

            st.session_state.selected_items = []
            st.session_state.selected_container = None

        except Exception as e:
            st.session_state.status_type = "error"
            st.session_state.status_msg = f"Failed to insert entry: {e}"
            st.session_state.response_json = None
    else:
        st.error("Please select all fields before submitting.")


if "selected_items" not in st.session_state:
    st.session_state.selected_items = []

if "selected_container" not in st.session_state:
    st.session_state.selected_container = None

if "selected_zone" not in st.session_state:
    st.session_state.selected_zone = None

if "selected_difficulty" not in st.session_state:
    st.session_state.selected_difficulty = None

with st.form("item_form"):
    st.title("Add New Loot")

    st.selectbox(
        "Select a zone",
        get_zones(),
        format_func=lambda x: x.name,
        key="selected_zone",
    )

    st.selectbox(
        "Select a difficulty",
        get_difficulties(),
        format_func=lambda x: x.name,
        key="selected_difficulty",
    )

    st.selectbox(
        "Select a container",
        get_containers(),
        format_func=lambda x: x.name,
        key="selected_container",
    )

    st.multiselect(
        "Select an item",
        get_items(),
        format_func=lambda x: x.name,
        key="selected_items",
    )

    submit_button = st.form_submit_button("Submit", on_click=process_submission)

if "status_msg" in st.session_state:
    if st.session_state.status_type == "success":
        st.success(st.session_state.status_msg)
        if "response_json" in st.session_state:
            st.json(st.session_state.response_json)
    elif st.session_state.status_type == "error":
        st.error(st.session_state.status_msg)
