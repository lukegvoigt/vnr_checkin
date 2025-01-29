import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import os

my_secret = os.environ['password']

# Initialize session state for attendees
if 'attendees' not in st.session_state:
    st.session_state.attendees = [
        {'id': '1000', 'name': 'Alice', 'checkedIn': False},
        {'id': '1001', 'name': 'Bob', 'checkedIn': False},
        {'id': '1002', 'name': 'Charlie', 'checkedIn': False},
        {'id': '1003', 'name': 'David', 'checkedIn': False},
        {'id': '1004', 'name': 'Eve', 'checkedIn': False},
    ]

def is_valid_attendee_id(id):
    """Validate if the ID is in the correct range"""
    try:
        num_id = int(id)
        return 1000 <= num_id <= 5000
    except ValueError:
        return False

def find_attendee(attendee_id):
    """Find attendee by ID"""
    return next(
        (attendee for attendee in st.session_state.attendees if attendee['id'] == attendee_id),
        None
    )

def process_check_in(attendee_id):
    """Process attendee check-in"""
    attendee = find_attendee(attendee_id)
    if attendee:
        if not attendee['checkedIn']:
            attendee['checkedIn'] = True
            return f"✅ {attendee['name']} checked in successfully!"
        return f"⚠️ {attendee['name']} is already checked in."
    return f"❌ Attendee ID {attendee_id} not found."

st.title("Event Check-in System")

tab1, tab2 = st.tabs(["📷 Check-in", "📋 Attendee List"])

with tab1:
    st.header("Scan QR Code")
    qr_code = qrcode_scanner(key='scanner')
    
    # Process QR code if one is detected
    if qr_code:
        if is_valid_attendee_id(qr_code):
            result = process_check_in(qr_code)
            st.write(result)
        else:
            st.error("Invalid QR code format. Please scan a valid attendee QR code.")
    
    # Manual Entry Section
    st.markdown("---")  # Add a visual separator
    st.subheader("Manual Code Entry")
    st.caption("If the scanner isn't working, enter the attendee code manually below:")
    
    # Create a form for manual entry
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
    # Create a dataframe from attendees
    attendee_data = [
        {"ID": a['id'], "Name": a['name'], "Status": "✅ Checked In" if a['checkedIn'] else "❌ Not Checked In"}
        for a in st.session_state.attendees
    ]
    st.table(attendee_data) 