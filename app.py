import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
import os
from datetime import datetime
import psycopg2
import pandas as pd

def get_attendee_info(code):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()

        # First check if the attendee exists and get their info
        cur.execute("""
            SELECT first_name, last_name, school_system, bringing_plus_one 
            FROM attendees 
            WHERE qr_code = %s
        """, (code,))

        result = cur.fetchone()

        if result:
            first_name, last_name, school_system, plus_one = result

            # First get current checked_in status without updating
            cur.execute("SELECT checked_in FROM attendees WHERE qr_code = %s", (code,))
            checked_in = cur.fetchone()[0]

            info = {
                'name': f"{first_name} {last_name}",
                'school_system': school_system,
                'plus_one': plus_one,
                'checked_in': checked_in
            }
            return info
        return None

    except Exception as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    # Prepare data for insertion
    data = [(
        str(row['ID']),
        row['Preferred Prefix (optional):'],
        row['First Name'],
        row['Last Name'],
        row['Suffix (e.g. Jr., III)'],
        row['School System'],
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
        school_system, grade_subject, 
        bringing_plus_one, email, status, school_cleaned,
        qr_code, attendance_response, checked_in
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        prefix = EXCLUDED.prefix,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        suffix = EXCLUDED.suffix,
        school_system = EXCLUDED.school_system,
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

# Initialize authentication state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = is_event_date()

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
            attendee = get_attendee_info(qr_code)
            if attendee:
                if attendee['checked_in'] > 0:
                    st.warning(f"Attendee already checked in: {attendee['name']} - {attendee['school_system']}")
                else:
                    st.markdown(":green[Found:]")
                    st.markdown(f":green[{attendee['name']}]")
                    st.markdown(f":green[{attendee['school_system']}]")
                if attendee['plus_one']:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("+1", key=f"plus_one_qr_{qr_code}", type="primary"):
                            try:
                                conn = psycopg2.connect(os.environ['DATABASE_URL'])
                                cur = conn.cursor()
                                cur.execute("""
                                    UPDATE attendees 
                                    SET checked_in = 2 
                                    WHERE qr_code = %s
                                """, (qr_code,))
                                conn.commit()
                            except Exception as e:
                                st.error(f"Error updating plus one status: {e}")
                            finally:
                                if cur:
                                    cur.close()
                                if conn:
                                    conn.close()
                            st.rerun()
                    with col2:
                        if attendee['checked_in'] == 2:
                            st.write(":green[(+1 added)]")

            else:
                st.error("Attendee not found")

        st.markdown("---")
        st.subheader("Manual Code Entry")
        st.caption("If the scanner isn't working, enter the attendee code manually below:")

        manual_attendee = None
        with st.form("manual_entry", clear_on_submit=True):
            manual_code = st.text_input("Enter Attendee Code:", 
                                      placeholder="Enter code (e.g., 1000)",
                                      help="Enter the number printed below the QR code")

            submit_button = st.form_submit_button("Check In", 
                                                use_container_width=True,
                                                type="primary")

            if submit_button and manual_code:
                manual_attendee = get_attendee_info(manual_code)
                if manual_attendee:
                    if manual_attendee['checked_in'] > 0:
                        st.warning(f"Attendee already checked in: {manual_attendee['name']} - {manual_attendee['school_system']}")
                    else:
                        st.markdown(":green[Found:]")
                        st.markdown(f":green[{manual_attendee['name']}]")
                        st.markdown(f":green[{manual_attendee['school_system']}]")
                        # Update check-in status after verification
                        try:
                            conn = psycopg2.connect(os.environ['DATABASE_URL'])
                            cur = conn.cursor()
                            cur.execute("""
                                UPDATE attendees 
                                SET checked_in = 1
                                WHERE qr_code = %s
                            """, (manual_code,))
                            conn.commit()
                        finally:
                            if cur: cur.close()
                            if conn: conn.close()
                else:
                    st.error("Attendee not found")

        if manual_code and manual_attendee and manual_attendee.get('plus_one'):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("+1", key=f"plus_one_manual_{manual_code}", type="primary"):
                    try:
                        conn = psycopg2.connect(os.environ['DATABASE_URL'])
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE attendees 
                            SET checked_in = 2 
                            WHERE qr_code = %s
                        """, (manual_code,))
                        conn.commit()
                    except Exception as e:
                        st.error(f"Error updating plus one status: {e}")
                    finally:
                        if cur:
                            cur.close()
                        if conn:
                            conn.close()
                    st.rerun()
            with col2:
                if manual_attendee['checked_in'] == 2:
                    st.write(":green[(+1 added)]")

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
                        prefix TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        suffix TEXT,
                        system TEXT,
                        grade TEXT,
                        plus_one BOOLEAN,
                        email TEXT,
                        status TEXT,
                        school TEXT,
                        id TEXT PRIMARY KEY
                    )
                """)

                # Insert data
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO tad_attendees 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) 
                        DO UPDATE SET 
                            prefix = EXCLUDED.prefix,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            suffix = EXCLUDED.suffix,
                            system = EXCLUDED.system,
                            grade = EXCLUDED.grade,
                            plus_one = EXCLUDED.plus_one,
                            email = EXCLUDED.email,
                            status = EXCLUDED.status,
                            school = EXCLUDED.school
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

        # Query and display attendees from database
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()

            cur.execute("""
                SELECT first_name, last_name, school_system, bringing_plus_one, checked_in 
                FROM attendees
                ORDER BY last_name, first_name
            """)

            attendees = cur.fetchall()

            # Convert to dataframe for display
            df = pd.DataFrame(attendees, 
                            columns=['First Name', 'Last Name', 'School System', 'Plus One', 'Checked In'])

            # Create status column based on checked_in value
            df['Status'] = df['Checked In'].map({
                0: "❌ Not Checked In",
                1: "✅ Checked In",
                2: "✅ Checked In with Plus One"
            })

            # Display the dataframe
            st.dataframe(df)

            # Add Plus One buttons for eligible attendees
            st.write("### Plus One Check-in")
            for idx, row in df.iterrows():
                if row['Plus One'] and row['Checked In'] == 1:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f":green[+ One] for {row['First Name']} {row['Last Name']}", key=f"plus_one_{idx}", type="primary"):
                            try:
                                conn = psycopg2.connect(os.environ['DATABASE_URL'])
                                cur = conn.cursor()
                                cur.execute("""
                                    UPDATE attendees 
                                    SET checked_in = 2 
                                    WHERE first_name = %s AND last_name = %s
                                """, (row['First Name'], row['Last Name']))
                                conn.commit()
                            except Exception as e:
                                st.error(f"Error updating plus one status: {e}")
                            finally:
                                if cur:
                                    cur.close()
                                if conn:
                                    conn.close()
                            st.rerun()
                    with col2:
                        if row['Checked In'] == 2:
                            st.write(":green[(+1 added)]")

        except Exception as e:
            st.error(f"Database error: {e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()