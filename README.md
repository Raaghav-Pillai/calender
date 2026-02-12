# Revamp "1+1" Availability Engine

A custom availability aggregator designed for **Revamp AI Consulting** to identify time slots where at least **one Primary** member and **one Secondary** member are simultaneously available.

## Features

- **Role-Based Input**: Users identify as "Primary" or "Secondary" before submitting
- **Date Window**: Feb 13th – Feb 21st, 2026
- **Time Slots**: 9:00 AM - 9:00 PM (30-minute intervals)
- **Interactive Grid**: Easy checkbox-style interface for selecting availability
- **Golden Window Logic**: Automatically identifies viable meeting times
- **Persistent Storage**: All submissions saved to `availability.json`

## Installation

1. Install Python (3.7 or higher)
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

## Running the Application

```bash
python -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## How to Use

### For Team Members (Input Availability)

1. Navigate to **Input Availability** in the sidebar
2. Enter your **Full Name**
3. Select your **Role** (Primary or Secondary)
4. Click on the grid cells to mark your available times
   - Rows = Time slots (9:00 AM - 9:00 PM)
   - Columns = Dates (Feb 13-21, 2026)
5. Click **Submit Availability**

### For Admin (View Results)

1. Navigate to **Admin Dashboard** in the sidebar
2. View the **Viable Time Slots** grid
   - **Green cells** = At least 1 Primary AND 1 Secondary available
   - **White cells** = Not viable (missing Primary or Secondary)
3. Check **Detailed Counts** tabs to see exact numbers

## Data Structure

Submissions are stored in `availability.json`:

```json
[
  {
    "name": "Alice",
    "role": "Primary",
    "availability": ["2026-02-13T09:00:00", "2026-02-13T09:30:00"],
    "timestamp": "2026-02-12T15:38:00.000000"
  }
]
```

## The "Golden Window" Logic

A time slot is considered **viable** if:
- **Primary Count >= 1** (at least one Primary member available)
- **AND Secondary Count >= 1** (at least one Secondary member available)

This ensures every meeting has the required mix of expertise.

## Team Size

Designed for 6 members total (mix of Primary and Secondary roles)

## Technical Stack

- **Python 3.13**
- **Streamlit 1.54.0** - Web framework
- **Pandas 2.3.3** - Data manipulation
- **JSON** - Data persistence

---

Built for **Revamp AI Consulting** | UIUC Student Organization
