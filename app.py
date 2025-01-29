import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import psycopg2
from psycopg2.extras import execute_values
import io
import pandas as pd

def setup_database():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Create attendees table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendees (
        id TEXT PRIMARY KEY,
        prefix TEXT,
        first_name TEXT,
        last_name TEXT,
        suffix TEXT,
        school_system TEXT,
        school_name TEXT,
        grade_subject TEXT,
        bringing_plus_one BOOLEAN,
        email TEXT,
        status TEXT,
        school_cleaned TEXT,
        qr_code TEXT,
        attendance_response TEXT,
        checked_in BOOLEAN DEFAULT FALSE
    )
    """)
    
    # Import CSV data
    df = pd.read_csv('attendees.csv')
    
    # Prepare data for insertion
    data = [(
        str(row['ID']),
        row['Preferred Prefix (optional):'],
        row['First Name'],
        row['Last Name'],
        row['Suffix (e.g. Jr., III)'],
        row['School System'],
        row['School Name'],
        row['Grade / Subject (e.g. 3rd Grade / 10th Grade Math)'],
        row['Bringing Plus One?'] == 'Yes',
        row['Preferred Contact Email'],
        row['Status'],
        row['School Cleaned'],
        row['qrCode'],
        row['Attendance Response'],
        False
    ) for _, row in df.iterrows()]
    
    # Insert data
    cur.executemany("""
    INSERT INTO attendees (
        id, prefix, first_name, last_name, suffix, 
        school_system, school_name, grade_subject, 
        bringing_plus_one, email, status, school_cleaned,
        qr_code, attendance_response, checked_in
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        prefix = EXCLUDED.prefix,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        suffix = EXCLUDED.suffix,
        school_system = EXCLUDED.school_system,
        school_name = EXCLUDED.school_name,
        grade_subject = EXCLUDED.grade_subject,
        bringing_plus_one = EXCLUDED.bringing_plus_one,
        email = EXCLUDED.email,
        status = EXCLUDED.status,
        school_cleaned = EXCLUDED.school_cleaned,
        qr_code = EXCLUDED.qr_code,
        attendance_response = EXCLUDED.attendance_response
    """, data)
    
    conn.commit()
    cur.close()
    conn.close()

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
    import pandas as pd
    df = pd.read_csv('attendees.csv')
    st.session_state.attendees = [
        {
            'id': str(row['ID']), 
            'name': f"{row['First Name']} {row['Last Name']}", 
            'checkedIn': False
        }
        for _, row in df.iterrows()
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

    def sync_from_csv():
        try:
            uploaded_file = st.file_uploader("Choose a CSV file", type='csv')
            if uploaded_file is not None:
                import pandas as pd
                
                
                # Read CSV
                df = pd.read_csv(uploaded_file)
                
                # Connect to PostgreSQL
                db_url = os.environ['DATABASE_URL']
                print(db_url)
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                
                # Create table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tad_attendees (
                        timestamp TEXT,
                        preferred_prefix TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        suffix TEXT,
                        school_system TEXT,
                        school_name TEXT,
                        grade_subject TEXT,
                        bringing_plus_one BOOLEAN,
                        email TEXT,
                        status TEXT,
                        school_cleaned TEXT,
                        id TEXT PRIMARY KEY,
                        qr_code TEXT,
                        attendance_response TEXT,
                        checked_in BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # Insert data
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO tad_attendees 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) 
                        DO UPDATE SET 
                            timestamp = EXCLUDED.timestamp,
                            preferred_prefix = EXCLUDED.preferred_prefix,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            suffix = EXCLUDED.suffix,
                            school_system = EXCLUDED.school_system,
                            school_name = EXCLUDED.school_name,
                            grade_subject = EXCLUDED.grade_subject,
                            bringing_plus_one = EXCLUDED.bringing_plus_one,
                            email = EXCLUDED.email,
                            status = EXCLUDED.status,
                            school_cleaned = EXCLUDED.school_cleaned,
                            qr_code = EXCLUDED.qr_code,
                            attendance_response = EXCLUDED.attendance_response
                    """, (
                        row['Timestamp'],
                        row['Preferred Prefix (optional):'],
                        row['First Name'],
                        row['Last Name'],
                        row['Suffix (e.g. Jr., III)'],
                        row['School System'],
                        row['School Name'],
                        row['Grade / Subject (e.g. 3rd Grade / 10th Grade Math)'],
                        row['Bringing Plus One?'] == 'Yes',
                        row['Preferred Contact Email'],
                        row['Status'],
                        row['School Cleaned'],
                        row['ID'],
                        row['qrCode'],
                        row['Attendance Response'],
                        False
                    ))
                
                conn.commit()
                cur.close()
                conn.close()
                
                # Update session state
                st.session_state.attendees = [
                    {
                        'id': str(row['ID']),
                        'name': f"{row['First Name']} {row['Last Name']}",
                        'checkedIn': False
                    }
                    for _, row in df.iterrows()
                ]
                return True
                
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")
            return False

    with tab2:
        st.header("Attendee List")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📤 Upload CSV", use_container_width=True):
                with st.spinner("Processing CSV..."):
                    if sync_from_csv():
                        st.success("CSV data uploaded successfully!")
        
        # Load and display full CSV data
        df = pd.read_csv('attendees.csv')
        # Create status mapping dictionary first
        status_mapping = {str(a['id']): "✅ Checked In" if a['checkedIn'] else "❌ Not Checked In" 
                         for a in st.session_state.attendees}
        df['Status'] = df['ID'].astype(str).map(status_mapping)
        st.dataframe(df)
        st.table(attendee_data)