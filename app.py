
import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import os
from datetime import datetime

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
    st.session_state.attendees = [
        {'id': '1000', 'name': 'Alice', 'checkedIn': False},
        {'id': '1001', 'name': 'Bob', 'checkedIn': False},
        {'id': '1002', 'name': 'Charlie', 'checkedIn': False},
        {'id': '1003', 'name': 'David', 'checkedIn': False},
        {'id': '1004', 'name': 'Eve', 'checkedIn': False},
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

    with tab2:
        st.header("Attendee List")
        attendee_data = [
            {"ID": a['id'], "Name": a['name'], "Status": "✅ Checked In" if a['checkedIn'] else "❌ Not Checked In"}
            for a in st.session_state.attendees
        ]
        st.table(attendee_data)
