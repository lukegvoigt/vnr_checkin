import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from psycopg2.extras import execute_values

# Get password from environment variables
my_secret = os.environ['password']

# Check if the date is February 4th, 2025
def is_event_date():
    today = datetime.now()
    return today.year == 2025 and today.month == 2 and today.day == 4

# Initialize session state for attendees and authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = is_event_date()

if 'attendees' not in st.session_state:
    # Initialize with some sample data
    st.session_state.attendees = [
        {'id': '1001', 'name': 'John Doe', 'checkedIn': False},
        {'id': '1002', 'name': 'Jane Smith', 'checkedIn': False},
        # Add more sample attendees as needed
    ]

def is_valid_attendee_id(id):
    try:
        num_id = int(id)
        return 1000 <= num_id <= 5000
    except ValueError:
        return False

def find_attendee(attendee_id):
    return next(
        (attendee for attendee in st.session_state.attendees if attendee['id'] == attendee_id),
        None
    )

def process_check_in(attendee_id):
    attendee = find_attendee(attendee_id)
    if attendee:
        if not attendee['checkedIn']:
            attendee['checkedIn'] = True
            return f"✅ {attendee['name']} checked in successfully!"
        return f"⚠️ {attendee['name']} is already checked in."
    return f"❌ Attendee ID {attendee_id} not found."

# Password authentication
if not st.session_state.authenticated:
    st.title("Event Check-in System")
    password = st.text_input("Enter password", type="password")
    if st.button("Login"):
        if password == my_secret:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
else:
    st.title("Event Check-in System")

    tab1, tab2 = st.tabs(["📷 Check-in", "📋 Attendee List"])

    with tab1:
        st.header("Scan QR Code")
        qr_code = qrcode_scanner(key='scanner')

        if qr_code:
            if is_valid_attendee_id(qr_code):
                result = process_check_in(qr_code)
                st.write(result)
            else:
                st.error("Invalid QR code format. Please scan a valid attendee QR code.")

        st.markdown("---")
        st.subheader("Manual Code Entry")
        st.caption("If the scanner isn't working, enter the attendee code manually below:")

        with st.form("manual_entry", clear_on_submit=True):
            manual_code = st.text_input("Enter Attendee Code:", 
                                      placeholder="Enter code (e.g., 1000)",
                                      help="Enter the number printed below the QR code")

            submit_button = st.form_submit_button("Check In", 
                                                use_container_width=True,
                                                type="primary")

            if submit_button and manual_code:
                if is_valid_attendee_id(manual_code):
                    result = process_check_in(manual_code)
                    st.write(result)
                else:
                    st.error("Please enter a valid attendee code (1000-5000)")

    def sync_databases():
        try:
            # Connect to Google Sheets
            sheets_creds = os.environ.get('GOOGLE_SHEETS_CREDS')
            sheet_url = os.environ.get('SHEET_URL')
            
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_info(
                eval(sheets_creds), 
                scopes=scopes
            )
            gc = gspread.authorize(credentials)
            sheet = gc.open_by_url(sheet_url).sheet1
            sheet_data = sheet.get_all_records()
            
            # Connect to PostgreSQL
            db_url = os.environ['DATABASE_URL']
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            # Create table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendees (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    checked_in BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Merge data
            for row in sheet_data:
                cur.execute("""
                    INSERT INTO attendees (id, name, checked_in)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        checked_in = EXCLUDED.checked_in
                """, (str(row['ID']), row['Name'], row['CheckedIn'] == 'TRUE'))
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Update session state
            st.session_state.attendees = [
                {'id': str(row['ID']), 'name': row['Name'], 'checkedIn': row['CheckedIn'] == 'TRUE'}
                for row in sheet_data
            ]
            return True
            
        except Exception as e:
            st.error(f"Sync failed: {str(e)}")
            return False

    with tab2:
        st.header("Attendee List")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Sync Database", use_container_width=True):
                with st.spinner("Syncing databases..."):
                    if sync_databases():
                        st.success("Databases synced successfully!")
        
        attendee_data = [
            {"ID": a['id'], "Name": a['name'], "Status": "✅ Checked In" if a['checkedIn'] else "❌ Not Checked In"}
            for a in st.session_state.attendees
        ]
        st.table(attendee_data)