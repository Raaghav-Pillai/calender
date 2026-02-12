import streamlit as st
import pandas as pd
import json
import os
import datetime
from datetime import timedelta

# --- Configuration ---
DATA_FILE = "availability.json"
START_DATE = datetime.date(2026, 2, 13)
END_DATE = datetime.date(2026, 2, 21)
START_HOUR = 9
END_HOUR = 21

st.set_page_config(page_title="Revamp Availability Engine", layout="wide")

# --- Helper Functions ---

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_date_range():
    delta = END_DATE - START_DATE
    return [START_DATE + timedelta(days=i) for i in range(delta.days + 1)]

def get_time_slots():
    slots = []
    current_time = datetime.datetime.combine(datetime.date.today(), datetime.time(START_HOUR, 0))
    end_time_today = datetime.datetime.combine(datetime.date.today(), datetime.time(END_HOUR, 0))
    
    while current_time < end_time_today:
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=30)
    return slots

# --- Page: Input Availability ---

def page_input():
    st.title("Member Availability Input")
    st.write("Please enter your name, role, and select your available times.")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name")
    with col2:
        role = st.radio("Role", ["Primary", "Secondary"])

    dates = get_date_range()
    date_strs = [d.strftime("%Y-%m-%d") for d in dates]
    time_slots = get_time_slots()

    # Create an empty DataFrame for the grid
    # Users will check boxes (True/False)
    # Rows: Time Slots, Columns: Dates
    df_template = pd.DataFrame(False, index=time_slots, columns=date_strs)

    st.subheader("Select Free Time Blocks")
    edited_df = st.data_editor(
        df_template,
        use_container_width=True,
        height=600,
        key="availability_grid"
    )

    if st.button("Submit Availability"):
        if not name:
            st.error("Please enter your name.")
            return

        # transform dataframe to list of overlapping intervals or just a list of datetime strings?
        # The PRD says: "slot_id": "2026-02-13T14:00:00"
        # We need to collect all True cells.
        
        selected_slots = []
        for date_col in date_strs:
            for time_row in time_slots:
                if edited_df.at[time_row, date_col]:
                    # Construct valid ISO datetime string
                    # Note: These are naive datetimes based on the agreed timezone (implied local or CST based on UIUC context)
                    slot_iso = f"{date_col}T{time_row}:00"
                    selected_slots.append(slot_iso)

        if not selected_slots:
            st.warning("You haven't selected any time slots.")
            return

        # Prepare payload
        entry = {
            "name": name,
            "role": role,
            "availability": selected_slots,
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Load existing data, remove old entry for this name if exists, and append new
        current_data = load_data()
        # Filter out previous submission by same name to allow updates
        current_data = [d for d in current_data if d["name"] != name]
        current_data.append(entry)
        
        save_data(current_data)
        st.success(f"Availability saved for {name} ({role})!")

# --- Page: Admin Dashboard ---

def page_admin():
    st.title("Admin Dashboard - Master Grid")
    
    data = load_data()
    st.metric("Total Submissions", len(data))

    if not data:
        st.info("No submissions yet.")
        return

    dates = get_date_range()
    date_strs = [d.strftime("%Y-%m-%d") for d in dates]
    time_slots = get_time_slots()

    # Initialize count grids
    # We need to count Primaries and Secondaries for each cell
    primary_counts = pd.DataFrame(0, index=time_slots, columns=date_strs)
    secondary_counts = pd.DataFrame(0, index=time_slots, columns=date_strs)
    
    # Store names for tooltips or detailed view
    slot_details = {} # Key: "date|time", Value: {"primaries": [], "secondaries": []}

    # Populate logic
    for entry in data:
        role = entry["role"]
        avail_slots = entry["availability"]
        
        for slot_iso in avail_slots:
            # slot_iso format: "YYYY-MM-DDTHH:MM:SS"
            parts = slot_iso.split("T")
            if len(parts) != 2:
                continue
            date_part = parts[0]
            time_part = parts[1][:5] # HH:MM
            
            if date_part in date_strs and time_part in time_slots:
                if role == "Primary":
                    primary_counts.at[time_part, date_part] += 1
                else:
                    secondary_counts.at[time_part, date_part] += 1
                
                key = f"{date_part}|{time_part}"
                if key not in slot_details:
                    slot_details[key] = {"primaries": [], "secondaries": []}
                
                if role == "Primary":
                    slot_details[key]["primaries"].append(entry["name"])
                else:
                    slot_details[key]["secondaries"].append(entry["name"])

    # Create Viability Grid
    # Condition: Primary >= 1 AND Secondary >= 1
    viability_grid = (primary_counts >= 1) & (secondary_counts >= 1)

    # Visualization
    st.subheader("Viable Time Slots (Golden Window)")
    st.caption("Green = At least 1 Primary and 1 Secondary available.")

    # We can use style to highlight text or background
    # But st.dataframe with styling is easier
    
    def highlight_viable(val):
        color = 'lightgreen' if val else 'white'
        return f'background-color: {color}'

    st.dataframe(viability_grid.style.map(highlight_viable), height=600, use_container_width=True)

    # Detailed view
    st.subheader("Detailed Counts")
    tab1, tab2 = st.tabs(["Primary Counts", "Secondary Counts"])
    with tab1:
        st.dataframe(primary_counts, use_container_width=True)
    with tab2:
        st.dataframe(secondary_counts, use_container_width=True)

# --- Main App Logic ---

def main():
    st.sidebar.title("Revamp Scheduling")
    page = st.sidebar.radio("Navigate", ["Input Availability", "Admin Dashboard"])

    if page == "Input Availability":
        page_input()
    else:
        page_admin()

if __name__ == "__main__":
    main()
