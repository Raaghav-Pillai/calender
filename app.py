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
        name = st.text_input("Full Name", key="input_name")
    with col2:
        role = st.radio("Role", ["Primary", "Secondary"], key="input_role")

    dates = get_date_range()
    date_strs = [d.strftime("%Y-%m-%d") for d in dates]
    date_labels = [d.strftime("%b %d") for d in dates]
    time_slots = get_time_slots()

    st.subheader("Select Free Time Blocks")
    st.caption("💡 **Tip:** Click and drag across cells to quickly select multiple time slots! Click a selected cell to deselect.")

    # Load existing data for this user if they're updating
    current_data = load_data()
    existing_entry = next((d for d in current_data if d["name"] == name), None)
    existing_slots = set(existing_entry["availability"]) if existing_entry else set()

    # Initialize session state for selections if not exists
    if 'selected_cells' not in st.session_state:
        st.session_state.selected_cells = existing_slots.copy()

    # Create interactive grid using HTML/CSS/JS with bidirectional communication
    grid_id = "availability_grid_v2"
    
    # Build the grid HTML
    grid_html = f"""
    <style>
        .availability-grid {{
            display: inline-block;
            border: 2px solid #4CAF50;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
            user-select: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .grid-row {{
            display: flex;
        }}
        .grid-cell {{
            width: 80px;
            height: 35px;
            border: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.15s ease;
            font-size: 11px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        .grid-header {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            font-weight: 600;
            cursor: default;
            font-size: 12px;
        }}
        .grid-time-label {{
            background-color: #f8f9fa;
            font-weight: 500;
            cursor: default;
            width: 70px;
            color: #495057;
        }}
        .grid-cell.selected {{
            background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
            color: white;
            font-weight: 600;
            transform: scale(0.95);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        }}
        .grid-cell.selectable:hover {{
            background-color: #E8F5E9;
            transform: scale(1.05);
        }}
        .grid-cell.selected:hover {{
            background: linear-gradient(135deg, #81C784 0%, #66BB6A 100%);
        }}
        .selection-count {{
            margin-top: 15px;
            padding: 10px 15px;
            background-color: #E3F2FD;
            border-left: 4px solid #2196F3;
            border-radius: 4px;
            font-weight: 500;
            color: #1976D2;
        }}
    </style>
    
    <div class="availability-grid" id="{grid_id}">
        <div class="grid-row">
            <div class="grid-cell grid-time-label"></div>
            {' '.join(f'<div class="grid-cell grid-header">{label}</div>' for label in date_labels)}
        </div>
        {''.join(f'''
        <div class="grid-row">
            <div class="grid-cell grid-time-label">{time_slot}</div>
            {' '.join(f'<div class="grid-cell selectable" data-slot="{date_str}T{time_slot}:00" onclick="toggleSlot(this)"></div>' for date_str in date_strs)}
        </div>
        ''' for time_slot in time_slots)}
    </div>
    
    <div class="selection-count" id="selectionCount">Selected: 0 time slots</div>
    
    <input type="hidden" id="selectedSlotsInput" value="">
    
    <script>
        let isMouseDown = false;
        let startMode = null;
        const selectedSlots = new Set({json.dumps(list(existing_slots))});
        
        const grid = document.getElementById('{grid_id}');
        const selectableCells = grid.querySelectorAll('.grid-cell.selectable');
        const countDisplay = document.getElementById('selectionCount');
        const hiddenInput = document.getElementById('selectedSlotsInput');
        
        // Initialize grid with existing selections
        function initializeGrid() {{
            selectableCells.forEach(cell => {{
                const slot = cell.getAttribute('data-slot');
                if (selectedSlots.has(slot)) {{
                    cell.classList.add('selected');
                    cell.textContent = '✓';
                }}
            }});
            updateCount();
        }}
        
        // Toggle individual slot
        function toggleSlot(cell) {{
            const slot = cell.getAttribute('data-slot');
            if (selectedSlots.has(slot)) {{
                selectedSlots.delete(slot);
                cell.classList.remove('selected');
                cell.textContent = '';
            }} else {{
                selectedSlots.add(slot);
                cell.classList.add('selected');
                cell.textContent = '✓';
            }}
            updateCount();
            updateHiddenInput();
        }}
        
        // Drag selection
        selectableCells.forEach(cell => {{
            cell.addEventListener('mousedown', (e) => {{
                e.preventDefault();
                isMouseDown = true;
                const slot = cell.getAttribute('data-slot');
                startMode = selectedSlots.has(slot) ? 'deselect' : 'select';
                applyMode(cell);
            }});
            
            cell.addEventListener('mouseenter', () => {{
                if (isMouseDown) {{
                    applyMode(cell);
                }}
            }});
            
            cell.addEventListener('mouseup', () => {{
                isMouseDown = false;
            }});
        }});
        
        document.addEventListener('mouseup', () => {{
            isMouseDown = false;
        }});
        
        function applyMode(cell) {{
            const slot = cell.getAttribute('data-slot');
            if (startMode === 'select' && !selectedSlots.has(slot)) {{
                selectedSlots.add(slot);
                cell.classList.add('selected');
                cell.textContent = '✓';
            }} else if (startMode === 'deselect' && selectedSlots.has(slot)) {{
                selectedSlots.delete(slot);
                cell.classList.remove('selected');
                cell.textContent = '';
            }}
            updateCount();
            updateHiddenInput();
        }}
        
        function updateCount() {{
            countDisplay.textContent = `Selected: ${{selectedSlots.size}} time slot${{selectedSlots.size !== 1 ? 's' : ''}}`;
        }}
        
        function updateHiddenInput() {{
            hiddenInput.value = JSON.stringify(Array.from(selectedSlots));
        }}
        
        // Make function globally accessible
        window.getSelectedSlots = function() {{
            return Array.from(selectedSlots);
        }};
        
        initializeGrid();
    </script>
    """
    
    st.components.v1.html(grid_html, height=750, scrolling=True)
    
    # Instructions
    st.markdown("---")
    st.markdown("### 📤 Submit Your Availability")
    
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.info("After selecting your time slots above, click the button to save your availability.")
    
    # Manual input as backup
    with st.expander("🔧 Advanced: Manual Input (if drag selection doesn't work)"):
        manual_slots = st.text_area(
            "Paste selected slots JSON here:",
            value="[]",
            height=100,
            key="manual_slots_input",
            help="If the drag selection isn't working, open browser console (F12), run: JSON.stringify(window.getSelectedSlots()), and paste the result here."
        )

    if st.button("✅ Submit Availability", type="primary", use_container_width=True):
        if not name:
            st.error("❌ Please enter your name.")
            return

        # Try to get selections from manual input first
        try:
            selected_slots = json.loads(manual_slots)
            if not selected_slots or selected_slots == []:
                st.warning("⚠️ No time slots selected. Please select at least one time slot.")
                st.info("💡 **Tip:** Open your browser console (press F12), run this command:\n\n`JSON.stringify(window.getSelectedSlots())`\n\nThen copy the output and paste it in the 'Advanced: Manual Input' section above.")
                return
        except:
            st.error("❌ Invalid selection data. Please use the manual input method in the Advanced section.")
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
        current_data = [d for d in current_data if d["name"] != name]
        current_data.append(entry)
        
        save_data(current_data)
        st.success(f"✅ Availability saved for **{name}** ({role})! You selected **{len(selected_slots)}** time slots.")
        st.balloons()

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
    primary_counts = pd.DataFrame(0, index=time_slots, columns=date_strs)
    secondary_counts = pd.DataFrame(0, index=time_slots, columns=date_strs)
    
    slot_details = {}

    # Populate logic
    for entry in data:
        role = entry["role"]
        avail_slots = entry["availability"]
        
        for slot_iso in avail_slots:
            parts = slot_iso.split("T")
            if len(parts) != 2:
                continue
            date_part = parts[0]
            time_part = parts[1][:5]
            
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
    viability_grid = (primary_counts >= 1) & (secondary_counts >= 1)

    # Visualization
    st.subheader("Viable Time Slots (Golden Window)")
    st.caption("Green = At least 1 Primary and 1 Secondary available.")

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
