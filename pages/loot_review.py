import time

import streamlit as st
import database as db
import pandas as pd

from models import GenaiItemDetails

st.set_page_config(page_title="Loot Review")
st.title("Loot Review")

# Select the next single record from the ai_add_loot table where status is
# PENDING and display the image on the page
ai_add_loot = db.get_single_ai_add_loot_by_status("PENDING")
if ai_add_loot:
    st.subheader(
        f"Reviewing a container that was opened in "
        f"{ai_add_loot.ai_add_loot_session.difficulty.name} "
        f"{ai_add_loot.ai_add_loot_session.zone.name} and "
        f" processed by genai on "
        f"{ai_add_loot.created_at.strftime('%Y-%m-%d %H:%M:%S')}."
    )
    st.image(st.secrets["AI_ADD_LOOT_IMAGE_URL"] + ai_add_loot.image_path)

st.write("GenAI Output:")
st.expander("GenAI Output JSON", expanded=False).write(
    ai_add_loot.genai_output_json.model_dump()
)

# Loop through the genai ouput and identify if more than 1 instance of the item
# "Koen" exists, if it does, they need to be combined with their quantities added
# together
koen_indices = []
koen_count = 0
koen_quantity = 0
for item in ai_add_loot.genai_output_json.items:
    if item.item_name.lower() == "koen":
        koen_count += 1
        koen_quantity += item.quantity
        koen_indices.append(ai_add_loot.genai_output_json.items.index(item))

if koen_count > 1:
    st.info(f"GenAI output contains {koen_count} instances of Koen.")
    st.info(f"Indices are {koen_indices}.")

    st.expander("Before combining Koen instances", expanded=False).write(
        ai_add_loot.genai_output_json.model_dump()
    )

    for index in sorted(koen_indices, reverse=True):
        del ai_add_loot.genai_output_json.items[index]

    ai_add_loot.genai_output_json.items.append(
        GenaiItemDetails(quantity=koen_quantity, item_name="Koen")
    )

    st.expander("After combining Koen instances", expanded=False).write(
        ai_add_loot.genai_output_json.model_dump()
    )

with st.container(border=True):
    st.subheader("Matching based on name_in_raid:")
    for i, item in enumerate(ai_add_loot.genai_output_json.items):
        dataframe_widget_key = f"name_in_raid_dataframe_{ai_add_loot.id}_{i}"
        name_in_raid_items = db.get_items_by_name_in_raid(item.item_name)
        st.caption(f"Matching items for {item.item_name} based on name_in_raid:")
        if name_in_raid_items:
            st.success(
                f"Found {len(name_in_raid_items)} matching item(s) "
                f"from name_in_raid for {item.item_name}:"
            )
            items_data = []
            for found_item in name_in_raid_items:
                items_data.append(
                    {
                        "ID": found_item.id,
                        "Name": found_item.name,
                        "Name in Raid": found_item.name_in_raid,
                        "Dimension X": found_item.dimension_x,
                        "Dimension Y": found_item.dimension_y,
                    }
                )
            st.dataframe(
                pd.DataFrame(items_data),
                key=dataframe_widget_key,
                on_select="rerun",
                selection_mode="single-row",
                width="stretch",
            )
        else:
            st.info(
                f"No matching items using name_in_raid "
                f"found in the database for {item.item_name}."
            )

st.divider()

with st.container(border=True):
    st.subheader("Matching based on name like:")
    for i, item in enumerate(ai_add_loot.genai_output_json.items):
        dataframe_widget_key = f"name_like_dataframe_{ai_add_loot.id}_{i}"
        name_like_items = db.get_items_like_name(item.item_name)
        st.caption(f"Matching items for {item.item_name} based on name like:")
        if name_like_items:
            st.success(
                f"Found {len(name_like_items)} matching item(s) "
                f"from name for {item.item_name}:"
            )
            items_data = []
            for found_item in name_like_items:
                items_data.append(
                    {
                        "ID": found_item.id,
                        "Name": found_item.name,
                        "Name in Raid": found_item.name_in_raid,
                        "Dimension X": found_item.dimension_x,
                        "Dimension Y": found_item.dimension_y,
                    }
                )

            st.dataframe(
                pd.DataFrame(items_data),
                key=dataframe_widget_key,
                on_select="rerun",
                selection_mode="single-row",
                width="stretch",
            )

        else:
            st.info(
                f"No matching items using name like "
                f"found in the database for {item.item_name}."
            )


st.divider()

st.subheader("Manual search through existing items to find match:")
for i, item in enumerate(ai_add_loot.genai_output_json.items):
    button_widget_key = f"fetch_all_items_{ai_add_loot.id}_{i}"
    dataframe_key = f"manual_dataframe_{ai_add_loot.id}_{i}"
    button_widget_flag = f"fetch_all_items_flag_{ai_add_loot.id}_{i}"

    if button_widget_flag not in st.session_state:
        st.session_state[button_widget_flag] = False

    if st.button(
        f"Fetch all items for manual review for {item.item_name}",
        width="stretch",
        key=button_widget_key,
    ):
        st.session_state[button_widget_flag] = True

    if st.session_state[button_widget_flag]:
        all_items = db.get_all_items()
        items_data = []
        if all_items:
            for found_item in all_items:
                items_data.append(
                    {
                        "ID": found_item.id,
                        "Name": found_item.name,
                        "Name in Raid": found_item.name_in_raid,
                        "Dimension X": found_item.dimension_x,
                        "Dimension Y": found_item.dimension_y,
                    }
                )

            st.dataframe(
                pd.DataFrame(items_data),
                key=dataframe_key,
                on_select="rerun",
                selection_mode="single-row",
                width="stretch",
            )

st.divider()
st.subheader("Final Selection and Approval")
final_selections = {}

for i, item in enumerate(ai_add_loot.genai_output_json.items):
    st.caption(f"Final selection for {item.item_name}:")
    current_item_selections = []
    name_in_raid_dataframe_key = f"name_in_raid_dataframe_{ai_add_loot.id}_{i}"
    name_like_dataframe_key = f"name_like_dataframe_{ai_add_loot.id}_{i}"
    manual_dataframe_key = f"manual_dataframe_{ai_add_loot.id}_{i}"

    if name_like_dataframe_key in st.session_state:
        selected_row_name_like = st.session_state[name_like_dataframe_key].get(
            "selection", {}.get("single-row")
        )
        if selected_row_name_like.get("rows"):
            current_name_like_items = db.get_items_like_name(item.item_name)
            st.toast("Ran get items like name query.")
            if current_name_like_items:
                selected_item = current_name_like_items[
                    selected_row_name_like["rows"][0]
                ]
                current_item_selections.append(selected_item)

    if name_in_raid_dataframe_key in st.session_state:
        selected_row_name_in_raid = st.session_state[name_in_raid_dataframe_key].get(
            "selection", {}.get("single-row")
        )
        if selected_row_name_in_raid.get("rows"):
            current_name_in_raid_items = db.get_items_by_name_in_raid(item.item_name)
            st.toast("Ran get items by name in raid query.")
            if current_name_in_raid_items:
                selected_item = current_name_in_raid_items[
                    selected_row_name_in_raid["rows"][0]
                ]
                current_item_selections.append(selected_item)

    if manual_dataframe_key in st.session_state:
        selected_row_manual = st.session_state[manual_dataframe_key].get(
            "selection", {}.get("single-row")
        )
        if selected_row_manual.get("rows") and all_items:
            all_items = db.get_all_items()
            st.toast("Ran get all items query.")
            if all_items:
                selected_item = all_items[selected_row_manual["rows"][0]]
                current_item_selections.append(selected_item)

    if len(current_item_selections) == 1:
        st.success(
            f"One item selected for {item.item_name}. "
            f"{current_item_selections[0].name} (ID: {current_item_selections[0].id}) "
            f"Marking for approval."
        )
        final_selected_item = current_item_selections[0]
        final_selections[i] = final_selected_item
    elif len(current_item_selections) > 1:
        st.warning(
            f"Multiple items selected for {item.item_name}. "
            f"Please select only one item for final approval."
        )
        final_selections[i] = None
    else:
        st.info(f"No item selected yet for {item.item_name}.")
        final_selections[i] = None

all_items_resolved = len(final_selections) > 0 and all(
    selection is not None for selection in final_selections.values()
)

if all_items_resolved:
    st.success("All items have been resolved and are ready for approval.")
    if st.button("Approve Loot", type="primary", width="stretch"):

        # First, if any of the selected items are missing a name_in_raid, update
        # the item in the database with the name_in_raid from GenAI output
        for i, selected_item in final_selections.items():
            if not selected_item.name_in_raid:
                response = db.update_item_name_in_raid(
                    selected_item.id, ai_add_loot.genai_output_json.items[i].item_name
                )
                st.write(response)
                if response:
                    st.toast(
                        f"Updated name_in_raid for item ID {selected_item.id} "
                        f"to {ai_add_loot.genai_output_json.items[i].item_name}."
                    )

        # Next, get the container record associated with the ai_add_loot record
        container = db.get_container_by_name(
            ai_add_loot.genai_output_json.container_name
        )

        if container:
            st.toast(
                f"Found container {container.name} with ID {container.id} "
                f"for container name {ai_add_loot.genai_output_json.container_name}."
            )
        else:
            st.error(
                f"No container found in the database with name "
                f"{ai_add_loot.genai_output_json.container_name}. "
                f"Cannot proceed with loot approval."
            )
            st.stop()

        # Then, create a new opening record in the database with all relevant fields
        opening = db.create_opening(
            ai_add_loot.id,
            ai_add_loot.ai_add_loot_session.difficulty.id,
            ai_add_loot.ai_add_loot_session.zone.id,
            container.id,
        )

        if opening:
            st.success(
                f"Created opening with ID {opening.id} for "
                f"difficulty id {opening.difficulty_id}, "
                f"zone id {opening.zone_id}, "
                f"and container id {opening.container_id}."
            )
            st.json(opening.model_dump())
        else:
            st.error(
                "Failed to create opening record. Cannot proceed with loot approval."
            )
            st.stop()

        # Finally, create the loot records associated to the opening
        for i, selected_item in final_selections.items():
            quantity = ai_add_loot.genai_output_json.items[i].quantity
            loot = db.create_loot(opening.id, selected_item.id, quantity)
            if loot:
                st.success(
                    f"Created loot record with ID {loot.id} for "
                    f"item {selected_item.name} (ID: {selected_item.id}), "
                    f"quantity {loot.quantity}."
                )
            else:
                # If a failure occurs here, we need to roll back the creation of
                # the opening and any other loot records

                st.error(
                    f"Failed to create loot record for item {selected_item.name} "
                    f"(ID: {selected_item.id})."
                )
                st.error("Rolling back opening and any created loot records.")
                db.delete_opening(opening.id)
                st.stop()

        # Update the ai_add_loot record to mark it as approved
        status_update = db.update_ai_add_loot_review_status(ai_add_loot.id, "APPROVED")
        if status_update:
            st.success(f"Updated ai_add_loot record ID {ai_add_loot.id} to APPROVED.")
            time.sleep(1)
            countdown_placeholder = st.empty()
            for i in range(5, 0, -1):
                countdown_placeholder.info(
                    f"Returning to loot review page in {i} seconds..."
                )
                time.sleep(1)
            st.rerun()
        else:
            st.error(
                f"Failed to update ai_add_loot record ID {ai_add_loot.id} to APPROVED."
            )
