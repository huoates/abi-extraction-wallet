import io

import streamlit as st
from PIL import Image, ImageOps
from storage3.exceptions import StorageApiError
from supabase import Client, create_client

from models import Item

supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"],
)


def get_next_item():
    response = (
        supabase.table("item")
        .select("*")
        .is_("thumbnail_url", "null")
        .limit(1)
        .execute()
    )
    return [
        Item.model_validate(item) for item in response.data
    ], response.model_dump_json()


def get_items_with_thumbnails():
    response = (
        supabase.table("item").select("*").not_.is_("thumbnail_url", "null").execute()
    )
    return [
        Item.model_validate(item) for item in response.data
    ], response.model_dump_json()


st.title("Add Item Image")
st.subheader("Next item missing thumbnail url is below")

with st.spinner():
    item, item_json = get_next_item()
    st.json(item_json)

with st.form("thumbnail_upload", clear_on_submit=True):
    uploaded_file = st.file_uploader(
        "Choose an image...", type=["jpg", "jpeg", "png", "gif"]
    )
    submit_button = st.form_submit_button("Update Item Thumbnail")

if submit_button:
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        width, height = img.size

        if width < 100 or height < 100:
            st.error(
                f"Your image is {width}x{height}. Image must be at least 100x100 pixels"
            )
            st.stop()

        cropped_img = ImageOps.fit(img, (100, 100), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        cropped_img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        try:
            response = supabase.storage.from_(
                st.secrets["SUPABASE_BUCKET_NAME"]
            ).upload(
                file=img_bytes,
                path=f"item_{item[0].id}.png",
                file_options={"content-type": "image/png"},
            )

            # Update the item's thumbnail_url in the database
            item_updated = (
                supabase.table("item")
                .update({"thumbnail_url": response.path})
                .eq("id", item[0].id)
                .execute()
            )

            if item_updated is not None:
                st.success("Item thumbnail_url updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update item thumbnail_url")
        except StorageApiError as e:
            st.error(f"Storage API error: {e}")
            if e.message == "The resource already exists":
                item_updated = (
                    supabase.table("item")
                    .update({"thumbnail_url": f"item_{item[0].id}.png"})
                    .eq("id", item[0].id)
                    .execute()
                )
                if item_updated is not None:
                    st.success("Item thumbnail_url updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update item thumbnail_url")
            else:
                st.error(f"Failed to upload image: {e}")
        except Exception as e:
            # Write the exact exception type in st.error
            st.error(f"Import from: {type(e).__module__}")
            st.error(f"Class name: {type(e).__name__}")
            st.error(f"Exception type: {type(e).__name__}")

st.divider()

# Display a nice list of items that have thumbnails
items, items_json = get_items_with_thumbnails()

# st.json(items_json)

for item in items:
    with st.container(border=True):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(
                st.secrets["PUBLIC_IMAGE_URL"] + item.thumbnail_url, width="content"
            )
        with col2:
            st.subheader(item.name)
            st.caption(f"Item ID: {item.id}")
