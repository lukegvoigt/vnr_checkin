import streamlit as st
import os
import psycopg2
from datetime import datetime
import random
import string
import bcrypt
import base64
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Sponsor Portal", page_icon="🎟️", layout="wide")

def get_gmail_access_token():
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = 'repl ' + repl_identity
    elif web_repl_renewal:
        x_replit_token = 'depl ' + web_repl_renewal
    else:
        return None
    
    try:
        response = requests.get(
            f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-mail',
            headers={
                'Accept': 'application/json',
                'X_REPLIT_TOKEN': x_replit_token
            }
        )
        data = response.json()
        connection = data.get('items', [{}])[0]
        settings = connection.get('settings', {})
        access_token = settings.get('access_token') or settings.get('oauth', {}).get('credentials', {}).get('access_token')
        return access_token
    except Exception as e:
        st.error(f"Error getting Gmail access: {e}")
        return None

def send_ticket_email(recipient_email, recipient_name, ticket_number, company_name):
    access_token = get_gmail_access_token()
    if not access_token:
        return False, "Gmail not connected"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #2c5282; color: white; padding: 20px; text-align: center;">
            <h1>Teacher Appreciation Dinner</h1>
            <p>Your Ticket</p>
        </div>
        <div style="padding: 20px; border: 1px solid #ddd;">
            <p>Dear {recipient_name},</p>
            <p>You have been invited to attend the <strong>Teacher Appreciation Dinner</strong> as a guest of <strong>{company_name}</strong>.</p>
            
            <div style="background-color: #f7fafc; border: 2px solid #2c5282; padding: 20px; margin: 20px 0; text-align: center;">
                <h2 style="color: #2c5282; margin: 0;">Ticket #{ticket_number}</h2>
            </div>
            
            <h3>Event Details:</h3>
            <ul>
                <li><strong>Date:</strong> {EVENT_DETAILS['date']}</li>
                <li><strong>Venue:</strong> {EVENT_DETAILS['venue']}</li>
                <li><strong>Address:</strong> {EVENT_DETAILS['address']}</li>
                <li><strong>Doors Open:</strong> {EVENT_DETAILS['doors_open']}</li>
                <li><strong>Dinner Served:</strong> {EVENT_DETAILS['dinner_served']}</li>
                <li><strong>Keynote Speaker:</strong> {EVENT_DETAILS['keynote_speaker']}</li>
            </ul>
            
            <p>Please present this email or your ticket number at check-in.</p>
            <p>We look forward to seeing you!</p>
        </div>
        <div style="background-color: #edf2f7; padding: 10px; text-align: center; font-size: 12px;">
            <p>Valdosta-North Rotary Teacher Appreciation Dinner</p>
        </div>
    </body>
    </html>
    """
    
    message = MIMEMultipart('alternative')
    message['To'] = recipient_email
    message['Subject'] = f"Your Ticket to the Teacher Appreciation Dinner - {EVENT_DETAILS['date']}"
    
    text_part = MIMEText(f"You are invited to the Teacher Appreciation Dinner. Ticket #{ticket_number}. Date: {EVENT_DETAILS['date']}. Venue: {EVENT_DETAILS['venue']}, {EVENT_DETAILS['address']}", 'plain')
    html_part = MIMEText(html_content, 'html')
    
    message.attach(text_part)
    message.attach(html_part)
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        response = requests.post(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            json={'raw': raw_message}
        )
        
        if response.status_code == 200:
            return True, "Email sent successfully"
        else:
            return False, f"Failed to send: {response.text}"
    except Exception as e:
        return False, str(e)

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
                    recipient_email = st.text_input("Recipient Email", key=f"email_{ticket_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        send_email_btn = st.form_submit_button("Send via Email", type="primary")
                    with col2:
                        print_ticket = st.form_submit_button("Print Ticket")
                    
                    if send_email_btn:
                        if not recipient_name:
                            st.error("Please enter recipient name")
                        elif not recipient_email:
                            st.error("Please enter recipient email")
                        else:
                            success, message = send_ticket_email(recipient_email, recipient_name, ticket_number, sponsor['company_name'])
                            if success:
                                update_ticket_email(ticket_id, recipient_email, recipient_name)
                                st.success(f"Ticket sent to {recipient_email}!")
                                st.rerun()
                            else:
                                st.error(f"Failed to send email: {message}")
                    
                    if print_ticket:
                        if recipient_name:
                            update_ticket_email(ticket_id, recipient_email if recipient_email else None, recipient_name)
                        mark_ticket_printed(ticket_id)
                        st.success("Ticket assigned! You can now print it below.")
                        st.rerun()
            
            st.markdown("### Print Preview")
            st.markdown(generate_printable_ticket(ticket_number, name, sponsor['company_name']), unsafe_allow_html=True)
