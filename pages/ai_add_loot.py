import hashlib
import io
import json

import streamlit as st
from google import genai
from PIL import Image
from supabase import Client, create_client

from models import Zone, Difficulty

supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"],
)


def reset_ai_add_loot():
    st.session_state.new_ai_add_loot = {
        "image_path": [],
        "image_hash": [],
        "session_id": None,
        "prompt_token_count": None,
        "candidates_token_count": None,
        "total_token_count": None,
        "status": None,
        "image_bytes": [],
        "ready_to_submit": False,
    }


def get_zones():
    response = supabase.table("zone").select("id, name").execute()
    return [Zone.model_validate(zone) for zone in response.data]


def get_difficulties():
    response = supabase.table("difficulty").select("id, name").execute()
    return [Difficulty.model_validate(difficulty) for difficulty in response.data]


if "new_ai_add_loot" not in st.session_state:
    reset_ai_add_loot()

# Define a flag that will be used in case a user uploads images that have all
# already been processed, we will use to display an error message
st.session_state.no_eligible_files_uploaded = False


def get_ai_add_loot_by_image_hash(image_hash):
    return (
        supabase.table("ai_add_loot").select("*").eq("image_hash", image_hash).execute()
    )


# Define a callback function to handle image uploads and populate session state
def handle_image_upload():
    for uploaded_file in st.session_state.uploaded_files:
        bytes_data = uploaded_file.getvalue()
        image_hash = hashlib.sha256(bytes_data).hexdigest()
        existing = get_ai_add_loot_by_image_hash(image_hash)

        if existing.data:
            st.error("Image already processed.")
            continue

        st.session_state.new_ai_add_loot["image_hash"].append(image_hash)
        st.session_state.new_ai_add_loot["image_bytes"].append(bytes_data)


if "selected_zone" not in st.session_state:
    st.session_state.selected_zone = None

if "selected_difficulty" not in st.session_state:
    st.session_state.selected_difficulty = None

PROMPT = """
For each image provided, extract inventory details.
Identify the container name from the top-left area.
For each distinct item shown, identify its name and its numerical quantity.
If an item's quantity is not explicitly visible, assume its quantity is 1.
If an item's quantity contains a slash (e.g. "80/80") assume its quantity is 1.

Output the extracted data as a JSON array.
Each object in the array will correspond to one of the input images, in the order they were provided.
Strictly adhere to the following schema:
```/dev/null/schema_multiple_images.json#L1-12
[
  {
    "container_name": "string",
    "items": [
      {
        "item_name": "string",
        "quantity": "integer"
      }
    ]
  }
]
"""

st.title("AI Add Loot")

client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

with st.form("ai_add_loot_form"):
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

    uploaded_files = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png", "gif"],
        accept_multiple_files=True,
    )

    submitted = st.form_submit_button("Process Loot")

    if submitted:
        st.session_state.no_eligible_files_uploaded = False

        for uploaded_file in uploaded_files:
            bytes_data = uploaded_file.getvalue()
            image_hash = hashlib.sha256(bytes_data).hexdigest()
            existing = get_ai_add_loot_by_image_hash(image_hash)

            if existing.data:
                st.error(
                    f"Image named {uploaded_file.name} with hash {image_hash} has already been processed."
                )
                continue

            st.session_state.new_ai_add_loot["image_hash"].append(image_hash)
            st.session_state.new_ai_add_loot["image_bytes"].append(bytes_data)

        if not st.session_state.new_ai_add_loot["image_hash"]:
            st.session_state.no_eligible_files_uploaded = True

        # If the image bytes are in session state, display the images that will
        # be processed to the user
        if st.session_state.new_ai_add_loot[
            "image_bytes"
        ]:  # Check if list is not empty
            num_images = len(st.session_state.new_ai_add_loot["image_bytes"])
            if num_images > 0:
                cols = st.columns(num_images)
                for i, image_byte in enumerate(
                    st.session_state.new_ai_add_loot["image_bytes"]
                ):
                    with cols[i]:
                        st.image(image_byte, width="stretch")

if st.session_state.no_eligible_files_uploaded:
    st.error("All uploaded images have already been processed.")
    if st.button("Reset", width="stretch"):
        reset_ai_add_loot()
        st.rerun()
    st.stop()

if not st.session_state.new_ai_add_loot["image_hash"]:
    st.info("Upload images and submit the form to process loot with Gen AI.")
    st.stop()

# If the image hash is in session state, this indicates that the image
# is ready to be processed, so display the button to the user
st.expander("Gemini Prompt", expanded=False).write(PROMPT)
if st.button("Submit to Gen AI", width="stretch"):
    with st.spinner("Gen AI Loading..."):
        try:
            images = [
                Image.open(io.BytesIO(image_bytes))
                for image_bytes in st.session_state.new_ai_add_loot["image_bytes"]
            ]
            contents = images + [PROMPT]
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=contents,
                config={"response_mime_type": "application/json"},
            )

            if response is None:
                st.error("No response from the model.")
                reset_ai_add_loot()

            st.session_state.new_ai_add_loot["genai_output_json"] = json.loads(
                response.text
            )

            st.subheader("Response:")
            st.json(response.text)

            prompt_token_count = None
            candidates_token_count = None
            total_token_count = None

            if response.usage_metadata:
                prompt_token_count = response.usage_metadata.prompt_token_count
                candidates_token_count = response.usage_metadata.candidates_token_count
                total_token_count = response.usage_metadata.total_token_count

            # Insert into ai_add_loot_sessions table
            session_data = {
                "prompt_token_count": prompt_token_count,
                "candidates_token_count": candidates_token_count,
                "total_token_count": total_token_count,
                "difficulty_id": st.session_state.selected_difficulty.id,
                "zone_id": st.session_state.selected_zone.id,
            }
            session_response = (
                supabase.table("ai_add_loot_session").insert(session_data).execute()
            )

            if not session_response.data:
                st.error("Failed to create session record.")
                reset_ai_add_loot()
                st.rerun()

            session_id = session_response.data[0]["id"]
            st.session_state.new_ai_add_loot["session_id"] = session_id

            image_paths = []
            for i, image_byte in enumerate(
                st.session_state.new_ai_add_loot["image_bytes"]
            ):
                image_hash = st.session_state.new_ai_add_loot["image_hash"][i]
                storage_response = supabase.storage.from_("ai-add-loot").upload(
                    file=image_byte,
                    path=f"{image_hash}.png",
                    file_options={"content-type": "image/png"},
                )
                image_paths.append(storage_response.path)

                # Insert into ai_add_loot table
                image_data = {
                    "session_id": session_id,
                    "image_path": storage_response.path,
                    "image_hash": image_hash,
                    "genai_output_json": st.session_state.new_ai_add_loot[
                        "genai_output_json"
                    ][i],
                    "review_status": "PENDING",
                }
                image_insert_response = (
                    supabase.table("ai_add_loot").insert(image_data).execute()
                )

                if not image_insert_response.data:
                    st.error(f"Failed to add image record for hash {image_hash}.")
                    # Depending on desired behavior, you might want to roll back the session or continue
                    reset_ai_add_loot()
                    st.rerun()

            st.success("Loot processed and records added successfully!")
            show_reset_button = True
            reset_ai_add_loot()

            if show_reset_button and st.button("Reset", width="stretch"):
                st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {e}")
            reset_ai_add_loot()
