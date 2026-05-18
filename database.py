import streamlit as st
from supabase import Client, create_client

from models import AiAddLoot, Container, Item, Loot, Opening

supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"],
)


def get_single_ai_add_loot_by_status(status):
    response = (
        supabase.table("ai_add_loot")
        .select("*, ai_add_loot_session(*, difficulty(*), zone(*))")
        .eq("review_status", status)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    if response.data:
        return AiAddLoot.model_validate(response.data[0])
    else:
        return None


def get_items_by_name_in_raid(name):
    response = (
        supabase.table("item")
        .select("*")
        .eq("name_in_raid", name)
        .order("name", desc=False)
        .execute()
    )
    if response.data:
        return [Item.model_validate(item) for item in response.data]
    else:
        return []


def get_items_like_name(name):
    response = (
        supabase.table("item")
        .select("*")
        .ilike("name", f"%{name}%")
        .order("name", desc=False)
        .execute()
    )
    if response.data:
        return [Item.model_validate(item) for item in response.data]
    else:
        return []


def get_all_items():
    response = supabase.table("item").select("*").order("name", desc=False).execute()
    if response.data:
        return [Item.model_validate(item) for item in response.data]
    else:
        return []


def update_item_name_in_raid(item_id, name_in_raid):
    """
    Update the name_in_raid field for an item in the database.
    Args:
        item_id (int): The ID of the item to update.
        name_in_raid (str): The new name_in_raid value to set.
    """
    response = (
        supabase.table("item")
        .update({"name_in_raid": name_in_raid})
        .eq("id", item_id)
        .execute()
    )
    return response


def get_container_by_name(name):
    response = (
        supabase.table("container")
        .select("*")
        .eq("name", name)
        .order("name", desc=False)
        .execute()
    )
    if response.data:
        return Container.model_validate(response.data[0])
    else:
        return None


def create_opening(ai_add_loot_id, difficulty_id, zone_id, container_id):
    response = (
        supabase.table("opening")
        .insert(
            {
                "ai_add_loot_id": ai_add_loot_id,
                "difficulty_id": difficulty_id,
                "zone_id": zone_id,
                "container_id": container_id,
            }
        )
        .execute()
    )
    if response.data:
        return Opening.model_validate(response.data[0])
    else:
        return None


def create_loot(opening_id, item_id, quantity):
    response = (
        supabase.table("loot")
        .insert(
            {
                "opening_id": opening_id,
                "item_id": item_id,
                "quantity": quantity,
            }
        )
        .execute()
    )
    if response.data:
        return Loot.model_validate(response.data[0])
    else:
        return None


def delete_opening(opening_id):
    response = supabase.table("opening").delete().eq("id", opening_id).execute()
    return response


def update_ai_add_loot_review_status(ai_add_loot_id, new_status):
    response = (
        supabase.table("ai_add_loot")
        .update({"review_status": new_status})
        .eq("id", ai_add_loot_id)
        .execute()
    )
    return response
