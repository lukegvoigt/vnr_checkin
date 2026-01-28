import streamlit as st
import os
import psycopg2
from datetime import datetime
import random
import string
import bcrypt

st.set_page_config(page_title="Sponsor Portal", page_icon="🎟️", layout="wide")

CURRENT_YEAR = 2026

EVENT_DETAILS = {
    "name": "Teacher Appreciation Dinner",
    "date": "Thursday, February 5th, 2026",
    "doors_open": "5:30 PM",
    "dinner_served": "6:00 PM",
    "end_time": "9:00 PM",
    "keynote_speaker": "Gerry Brooks",
    "venue": "Rainwater Conference Center",
    "address": "1 Meeting Pl, Valdosta, GA 31601"
}

def generate_ticket_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_sponsor_info(username, password):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            SELECT id, company_name, sponsor_level, total_seats, year, password
            FROM sponsors
            WHERE username = %s AND year = %s
        """, (username, CURRENT_YEAR))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            stored_password = result[5]
            if stored_password.startswith('$2'):
                if not verify_password(password, stored_password):
                    return None
            else:
                if password != stored_password:
                    return None
            return {
                'id': result[0],
                'company_name': result[1],
                'sponsor_level': result[2],
                'total_seats': result[3],
                'year': result[4]
            }
        return None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

def get_sponsor_tickets(sponsor_id):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            SELECT id, ticket_number, recipient_email, recipient_name, sent_at, printed_at
            FROM sponsor_tickets
            WHERE sponsor_id = %s AND year = %s
            ORDER BY id
        """, (sponsor_id, CURRENT_YEAR))
        tickets = cur.fetchall()
        cur.close()
        conn.close()
        return tickets
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def create_tickets_for_sponsor(sponsor_id, total_seats):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sponsor_tickets WHERE sponsor_id = %s AND year = %s", (sponsor_id, CURRENT_YEAR))
        existing = cur.fetchone()[0]
        
        if existing < total_seats:
            for _ in range(total_seats - existing):
                ticket_number = generate_ticket_number()
                cur.execute("""
                    INSERT INTO sponsor_tickets (sponsor_id, ticket_number, year)
                    VALUES (%s, %s, %s)
                """, (sponsor_id, ticket_number, CURRENT_YEAR))
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Error creating tickets: {e}")

def update_ticket_email(ticket_id, email, name):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            UPDATE sponsor_tickets
            SET recipient_email = %s, recipient_name = %s, sent_at = %s
            WHERE id = %s
        """, (email, name, datetime.now(), ticket_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating ticket: {e}")
        return False

def mark_ticket_printed(ticket_id):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            UPDATE sponsor_tickets
            SET printed_at = %s
            WHERE id = %s
        """, (datetime.now(), ticket_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error marking ticket as printed: {e}")
        return False

def generate_printable_ticket(ticket_number, recipient_name, company_name):
    return f"""
    <div style="border: 2px solid #333; padding: 20px; margin: 10px; max-width: 400px; font-family: Arial, sans-serif;">
        <h2 style="text-align: center; color: #2c5282;">{EVENT_DETAILS['name']}</h2>
        <hr>
        <p><strong>Guest:</strong> {recipient_name if recipient_name else 'TBD'}</p>
        <p><strong>Sponsored by:</strong> {company_name}</p>
        <p><strong>Ticket #:</strong> {ticket_number}</p>
        <hr>
        <p><strong>Date:</strong> {EVENT_DETAILS['date']}</p>
        <p><strong>Venue:</strong> {EVENT_DETAILS['venue']}</p>
        <p><strong>Address:</strong> {EVENT_DETAILS['address']}</p>
        <p><strong>Doors Open:</strong> {EVENT_DETAILS['doors_open']}</p>
        <p><strong>Dinner Served:</strong> {EVENT_DETAILS['dinner_served']}</p>
        <p><strong>Keynote Speaker:</strong> {EVENT_DETAILS['keynote_speaker']}</p>
    </div>
    """

if 'sponsor_authenticated' not in st.session_state:
    st.session_state.sponsor_authenticated = False
if 'sponsor_info' not in st.session_state:
    st.session_state.sponsor_info = None

st.title("Sponsor Portal")
st.subheader(EVENT_DETAILS['name'])

if not st.session_state.sponsor_authenticated:
    st.write("Please log in with your sponsor credentials.")
    
    with st.form("sponsor_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            sponsor = get_sponsor_info(username, password)
            if sponsor:
                st.session_state.sponsor_authenticated = True
                st.session_state.sponsor_info = sponsor
                create_tickets_for_sponsor(sponsor['id'], sponsor['total_seats'])
                st.rerun()
            else:
                st.error("Invalid username or password")
else:
    sponsor = st.session_state.sponsor_info
    
    if st.button("Logout"):
        st.session_state.sponsor_authenticated = False
        st.session_state.sponsor_info = None
        st.rerun()
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Company", sponsor['company_name'])
    with col2:
        st.metric("Sponsor Level", sponsor['sponsor_level'])
    with col3:
        st.metric("Total Seats", sponsor['total_seats'])
    
    st.markdown("---")
    st.subheader("Event Details")
    st.write(f"**Date:** {EVENT_DETAILS['date']}")
    st.write(f"**Venue:** {EVENT_DETAILS['venue']}, {EVENT_DETAILS['address']}")
    st.write(f"**Doors Open:** {EVENT_DETAILS['doors_open']} | **Dinner:** {EVENT_DETAILS['dinner_served']} | **End:** {EVENT_DETAILS['end_time']}")
    st.write(f"**Keynote Speaker:** {EVENT_DETAILS['keynote_speaker']}")
    
    st.markdown("---")
    st.subheader("Your Tickets")
    
    tickets = get_sponsor_tickets(sponsor['id'])
    
    assigned_count = sum(1 for t in tickets if t[2] or t[5])
    st.write(f"**Assigned:** {assigned_count} / {sponsor['total_seats']}")
    
    for ticket in tickets:
        ticket_id, ticket_number, email, name, sent_at, printed_at = ticket
        
        with st.expander(f"Ticket {ticket_number} - {'Assigned' if email or printed_at else 'Available'}"):
            if email:
                st.write(f"**Recipient:** {name}")
                st.write(f"**Email:** {email}")
                st.write(f"**Sent:** {sent_at}")
            elif printed_at:
                st.write(f"**Recipient:** {name if name else 'Not specified'}")
                st.write(f"**Printed:** {printed_at}")
            else:
                with st.form(f"assign_{ticket_id}"):
                    recipient_name = st.text_input("Recipient Name", key=f"name_{ticket_id}")
                    recipient_email = st.text_input("Recipient Email (for your records)", key=f"email_{ticket_id}")
                    
                    print_ticket = st.form_submit_button("Assign & Print Ticket", type="primary")
                    
                    if print_ticket:
                        if recipient_name:
                            update_ticket_email(ticket_id, recipient_email if recipient_email else None, recipient_name)
                        mark_ticket_printed(ticket_id)
                        st.success("Ticket assigned! You can now print it below.")
                        st.rerun()
            
            st.markdown("### Print Preview")
            st.markdown(generate_printable_ticket(ticket_number, name, sponsor['company_name']), unsafe_allow_html=True)
