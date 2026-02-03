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
import qrcode
from io import BytesIO

st.set_page_config(page_title="Sponsor Portal", page_icon="🎟️", layout="wide")

def get_gmail_access_token():
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN')
    
    if client_id and client_secret and refresh_token:
        try:
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            if response.status_code == 200:
                return response.json().get('access_token')
        except Exception as e:
            st.error(f"Error refreshing token: {e}")
            return None
    
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
    
    qr_base64 = generate_qr_code_base64(ticket_number)
    
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
                <img src="data:image/png;base64,{qr_base64}" alt="QR Code" style="width: 150px; height: 150px;">
                <h2 style="color: #2c5282; margin: 10px 0; font-size: 32px; letter-spacing: 5px;">{ticket_number}</h2>
                <p style="color: #666; font-size: 12px;">Scan QR code or provide this number at check-in</p>
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
    
    sender_email = os.environ.get('GMAIL_SENDER_EMAIL', 'noreply@example.com')
    sender_name = os.environ.get('GMAIL_SENDER_NAME', 'Valdosta-North Rotary')
    
    message = MIMEMultipart('alternative')
    message['From'] = f"{sender_name} <{sender_email}>"
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
    return str(random.randint(10000, 99999))

def generate_qr_code_base64(ticket_number):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(ticket_number)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

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
    qr_base64 = generate_qr_code_base64(ticket_number)
    ticket_html = f"""
    <div id="ticket-{ticket_number}" style="border: 2px solid #333; padding: 20px; margin: 10px; max-width: 400px; font-family: Arial, sans-serif;">
        <h2 style="text-align: center; color: #2c5282;">{EVENT_DETAILS['name']}</h2>
        <hr>
        <div style="text-align: center; margin: 15px 0;">
            <img src="data:image/png;base64,{qr_base64}" alt="QR Code" style="width: 150px; height: 150px;">
            <h3 style="margin: 10px 0; font-size: 24px; letter-spacing: 3px;">{ticket_number}</h3>
        </div>
        <hr>
        <p><strong>Guest:</strong> {recipient_name if recipient_name else '_______________________'}</p>
        <p><strong>Sponsored by:</strong> {company_name}</p>
        <hr>
        <p><strong>Date:</strong> {EVENT_DETAILS['date']}</p>
        <p><strong>Venue:</strong> {EVENT_DETAILS['venue']}</p>
        <p><strong>Address:</strong> {EVENT_DETAILS['address']}</p>
        <p><strong>Doors Open:</strong> {EVENT_DETAILS['doors_open']} | <strong>End Time:</strong> {EVENT_DETAILS['end_time']}</p>
        <p><strong>Dinner Served:</strong> {EVENT_DETAILS['dinner_served']}</p>
        <p><strong>Keynote Speaker:</strong> {EVENT_DETAILS['keynote_speaker']}</p>
        <hr>
        <p style="text-align: center; font-style: italic; color: #666;"><strong>This ticket is valid for one adult entry only.</strong></p>
    </div>
    """
    return ticket_html

def generate_printable_html_file(ticket_number, recipient_name, company_name):
    qr_base64 = generate_qr_code_base64(ticket_number)
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Ticket {ticket_number}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .ticket {{ border: 2px solid #333; padding: 20px; max-width: 400px; margin: auto; }}
        h2 {{ text-align: center; color: #2c5282; }}
        .qr-section {{ text-align: center; margin: 15px 0; }}
        .ticket-number {{ font-size: 24px; letter-spacing: 3px; margin: 10px 0; }}
        .valid-note {{ text-align: center; font-style: italic; color: #666; }}
        @media print {{
            body {{ margin: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body onload="window.print();">
    <div class="ticket">
        <h2>{EVENT_DETAILS['name']}</h2>
        <hr>
        <div class="qr-section">
            <img src="data:image/png;base64,{qr_base64}" alt="QR Code" style="width: 150px; height: 150px;">
            <h3 class="ticket-number">{ticket_number}</h3>
        </div>
        <hr>
        <p><strong>Guest:</strong> {recipient_name if recipient_name else '_______________________'}</p>
        <p><strong>Sponsored by:</strong> {company_name}</p>
        <hr>
        <p><strong>Date:</strong> {EVENT_DETAILS['date']}</p>
        <p><strong>Venue:</strong> {EVENT_DETAILS['venue']}</p>
        <p><strong>Address:</strong> {EVENT_DETAILS['address']}</p>
        <p><strong>Doors Open:</strong> {EVENT_DETAILS['doors_open']} | <strong>End Time:</strong> {EVENT_DETAILS['end_time']}</p>
        <p><strong>Dinner Served:</strong> {EVENT_DETAILS['dinner_served']}</p>
        <p><strong>Keynote Speaker:</strong> {EVENT_DETAILS['keynote_speaker']}</p>
        <hr>
        <p class="valid-note"><strong>This ticket is valid for one adult entry only.</strong></p>
    </div>
</body>
</html>"""

def generate_all_tickets_html(tickets, company_name):
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>All Tickets</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .ticket { 
            border: 2px solid #333; 
            padding: 20px; 
            max-width: 400px; 
            margin: 20px auto;
            page-break-after: always;
        }
        .ticket:last-child { page-break-after: avoid; }
        h2 { text-align: center; color: #2c5282; margin-top: 0; }
        .qr-section { text-align: center; margin: 15px 0; }
        .ticket-number { font-size: 24px; letter-spacing: 3px; margin: 10px 0; }
        .valid-note { text-align: center; font-style: italic; color: #666; }
        @media print {
            body { margin: 0; }
            .ticket { margin: 0 auto; border: 2px solid #333; }
        }
    </style>
</head>
<body onload="window.print();">
"""
    
    for ticket in tickets:
        ticket_id, ticket_number, email, name, sent_at, printed_at = ticket
        qr_base64 = generate_qr_code_base64(ticket_number)
        html_content += f"""
    <div class="ticket">
        <h2>{EVENT_DETAILS['name']}</h2>
        <hr>
        <div class="qr-section">
            <img src="data:image/png;base64,{qr_base64}" alt="QR Code" style="width: 150px; height: 150px;">
            <h3 class="ticket-number">{ticket_number}</h3>
        </div>
        <hr>
        <p><strong>Guest:</strong> {name if name else '_______________________'}</p>
        <p><strong>Sponsored by:</strong> {company_name}</p>
        <hr>
        <p><strong>Date:</strong> {EVENT_DETAILS['date']}</p>
        <p><strong>Venue:</strong> {EVENT_DETAILS['venue']}</p>
        <p><strong>Address:</strong> {EVENT_DETAILS['address']}</p>
        <p><strong>Doors Open:</strong> {EVENT_DETAILS['doors_open']} | <strong>End Time:</strong> {EVENT_DETAILS['end_time']}</p>
        <p><strong>Dinner Served:</strong> {EVENT_DETAILS['dinner_served']}</p>
        <p><strong>Keynote Speaker:</strong> {EVENT_DETAILS['keynote_speaker']}</p>
        <hr>
        <p class="valid-note"><strong>This ticket is valid for one adult entry only.</strong></p>
    </div>
"""
    
    html_content += """
</body>
</html>"""
    return html_content

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'rotaryadmin2026')

def add_sponsor(username, password, company_name, sponsor_level, total_seats):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sponsors (username, password, company_name, sponsor_level, total_seats, year)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, password, company_name, sponsor_level, total_seats, CURRENT_YEAR))
        sponsor_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return sponsor_id, None
    except Exception as e:
        return None, str(e)

def delete_sponsor(sponsor_id):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("DELETE FROM sponsor_tickets WHERE sponsor_id = %s AND year = %s", (sponsor_id, CURRENT_YEAR))
        cur.execute("DELETE FROM sponsors WHERE id = %s AND year = %s", (sponsor_id, CURRENT_YEAR))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def update_sponsor_password(sponsor_id, new_password):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("UPDATE sponsors SET password = %s WHERE id = %s AND year = %s", 
                    (new_password, sponsor_id, CURRENT_YEAR))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def get_sponsor_tickets_admin(sponsor_id):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            SELECT id, ticket_number, recipient_name, recipient_email, sent_at, printed_at
            FROM sponsor_tickets
            WHERE sponsor_id = %s AND year = %s
            ORDER BY id
        """, (sponsor_id, CURRENT_YEAR))
        tickets = cur.fetchall()
        cur.close()
        conn.close()
        return tickets
    except Exception as e:
        return []

def update_ticket_admin(ticket_id, recipient_name, recipient_email):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            UPDATE sponsor_tickets 
            SET recipient_name = %s, recipient_email = %s
            WHERE id = %s
        """, (recipient_name if recipient_name else None, recipient_email if recipient_email else None, ticket_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def mark_ticket_printed_admin(ticket_id):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            UPDATE sponsor_tickets 
            SET printed_at = NOW()
            WHERE id = %s
        """, (ticket_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def get_all_sponsors():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, company_name, sponsor_level, total_seats
            FROM sponsors
            WHERE year = %s
            ORDER BY sponsor_level, company_name
        """, (CURRENT_YEAR,))
        sponsors = cur.fetchall()
        cur.close()
        conn.close()
        return sponsors
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def get_all_tickets_for_sponsor(sponsor_id):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("""
            SELECT ticket_number, recipient_name, recipient_email, sent_at, printed_at
            FROM sponsor_tickets
            WHERE sponsor_id = %s AND year = %s
            ORDER BY id
        """, (sponsor_id, CURRENT_YEAR))
        tickets = cur.fetchall()
        cur.close()
        conn.close()
        return tickets
    except Exception as e:
        return []

if 'sponsor_authenticated' not in st.session_state:
    st.session_state.sponsor_authenticated = False
if 'sponsor_info' not in st.session_state:
    st.session_state.sponsor_info = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

query_params = st.query_params
url_username = query_params.get("sponsor", None)

st.title("Sponsor Portal")
st.subheader(EVENT_DETAILS['name'])

if not st.session_state.sponsor_authenticated and not st.session_state.is_admin:
    if url_username:
        st.write(f"Welcome! Please enter your password to continue.")
        
        with st.form("sponsor_login_simple"):
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                sponsor = get_sponsor_info(url_username, password)
                if sponsor:
                    st.session_state.sponsor_authenticated = True
                    st.session_state.sponsor_info = sponsor
                    create_tickets_for_sponsor(sponsor['id'], sponsor['total_seats'])
                    st.rerun()
                else:
                    st.error("Invalid password")
    else:
        st.write("Please log in with your sponsor credentials.")
        
        with st.form("sponsor_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    sponsor = get_sponsor_info(username, password)
                    if sponsor:
                        st.session_state.sponsor_authenticated = True
                        st.session_state.sponsor_info = sponsor
                        create_tickets_for_sponsor(sponsor['id'], sponsor['total_seats'])
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

elif st.session_state.is_admin:
    if st.button("Logout"):
        st.session_state.is_admin = False
        st.rerun()
    
    st.markdown("---")
    st.header("Admin Dashboard")
    
    sponsors = get_all_sponsors()
    
    total_sponsors = len(sponsors)
    total_seats = sum(s[4] for s in sponsors)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Sponsors", total_sponsors)
    with col2:
        st.metric("Total Seats", total_seats)
    
    st.markdown("---")
    st.subheader("Add New Sponsor")
    
    with st.form("add_sponsor_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_company = st.text_input("Company Name")
            new_username = st.text_input("Username (for login)")
            new_password = st.text_input("Password (for login)")
        with col2:
            new_level = st.selectbox("Sponsor Level", ["Diamond", "Platinum", "Gold", "Silver"])
            new_seats = st.number_input("Number of Seats", min_value=1, max_value=50, value=10)
        
        add_btn = st.form_submit_button("Add Sponsor", type="primary")
        
        if add_btn:
            if not new_company or not new_username or not new_password:
                st.error("Please fill in all fields")
            else:
                sponsor_id, error = add_sponsor(new_username, new_password, new_company, new_level, new_seats)
                if sponsor_id:
                    st.success(f"Added sponsor: {new_company}")
                    st.rerun()
                else:
                    st.error(f"Failed to add sponsor: {error}")
    
    st.markdown("---")
    st.subheader("Export Sponsor Seating CSV")
    
    if st.button("Generate Sponsor Seating CSV"):
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cur = conn.cursor()
            cur.execute("""
                SELECT s.username, st.ticket_number
                FROM sponsor_tickets st
                JOIN sponsors s ON st.sponsor_id = s.id
                WHERE st.year = %s
                ORDER BY s.username, st.id
            """, (CURRENT_YEAR,))
            all_tickets = cur.fetchall()
            cur.close()
            conn.close()
            
            csv_rows = ["Name,Email,Type,School System,ticket_id,Table"]
            username_counts = {}
            
            for username, ticket_number in all_tickets:
                if username not in username_counts:
                    username_counts[username] = 0
                username_counts[username] += 1
                guest_num = username_counts[username]
                
                name = f"{username} Guest {guest_num}"
                csv_rows.append(f"{name},N/A,Sponsor,N/A,{ticket_number},")
            
            csv_content = "\n".join(csv_rows)
            st.download_button(
                label="Download Sponsor Seating CSV",
                data=csv_content,
                file_name="sponsor_seating.csv",
                mime="text/csv"
            )
            st.success(f"Generated {len(all_tickets)} sponsor tickets!")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    st.subheader("All Sponsors")
    
    level_order = {'Diamond': 1, 'Platinum': 2, 'Gold': 3, 'Silver': 4}
    sponsors_sorted = sorted(sponsors, key=lambda x: (level_order.get(x[3], 99), x[2]))
    
    for sponsor in sponsors_sorted:
        sponsor_id, username, company_name, level, seats = sponsor
        tickets = get_all_tickets_for_sponsor(sponsor_id)
        assigned = sum(1 for t in tickets if t[1] or t[3] or t[4])
        
        with st.expander(f"{company_name} ({level}) - {assigned}/{seats} assigned"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**Username:** {username}")
                st.write(f"**Level:** {level} | **Seats:** {seats} | **Assigned:** {assigned}")
            with col2:
                new_pw = st.text_input("New Password", key=f"pw_{sponsor_id}", placeholder="Enter new password")
                if st.button("Change Password", key=f"pwbtn_{sponsor_id}"):
                    if new_pw:
                        success, error = update_sponsor_password(sponsor_id, new_pw)
                        if success:
                            st.success("Password updated!")
                            st.rerun()
                        else:
                            st.error(f"Failed: {error}")
                    else:
                        st.warning("Enter a password first")
            with col3:
                if st.button("Delete Sponsor", key=f"del_{sponsor_id}", type="secondary"):
                    success, error = delete_sponsor(sponsor_id)
                    if success:
                        st.success(f"Deleted {company_name}")
                        st.rerun()
                    else:
                        st.error(f"Failed: {error}")
            
            st.markdown("---")
            st.write("**Tickets:**")
            
            admin_tickets = get_sponsor_tickets_admin(sponsor_id)
            
            if not admin_tickets:
                create_tickets_for_sponsor(sponsor_id, seats)
                admin_tickets = get_sponsor_tickets_admin(sponsor_id)
            
            for tkt in admin_tickets:
                tkt_id, ticket_num, tkt_name, tkt_email, sent, printed = tkt
                
                tcol1, tcol2, tcol3, tcol4 = st.columns([1, 2, 2, 1])
                with tcol1:
                    st.write(f"**{ticket_num}**")
                    if sent:
                        st.caption("Emailed")
                    elif printed:
                        st.caption("Printed")
                with tcol2:
                    new_name = st.text_input("Guest Name", value=tkt_name or "", key=f"name_{tkt_id}", label_visibility="collapsed", placeholder="Guest name")
                with tcol3:
                    new_email = st.text_input("Email", value=tkt_email or "", key=f"email_{tkt_id}", label_visibility="collapsed", placeholder="Email (optional)")
                with tcol4:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("Save", key=f"save_{tkt_id}"):
                            success, error = update_ticket_admin(tkt_id, new_name, new_email)
                            if success:
                                st.rerun()
                    with btn_col2:
                        ticket_html = generate_printable_html_file(ticket_num, new_name or "", company_name)
                        st.download_button(
                            "Print",
                            ticket_html,
                            file_name=f"ticket_{ticket_num}.html",
                            mime="text/html",
                            key=f"print_{tkt_id}",
                            on_click=lambda tid=tkt_id: mark_ticket_printed_admin(tid)
                        )
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
    
    if tickets:
        all_tickets_html = generate_all_tickets_html(tickets, sponsor['company_name'])
        st.download_button(
            label="Print All Tickets",
            data=all_tickets_html,
            file_name=f"all_tickets_{sponsor['company_name'].replace(' ', '_')}.html",
            mime="text/html",
            help="Download and open to print all tickets at once (one per page)",
            type="primary"
        )
    
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
                    
                    send_email_btn = st.form_submit_button("Send via Email", type="primary")
                    
                    if send_email_btn:
                        if not recipient_name:
                            st.error("Please enter recipient name")
                        elif not recipient_email:
                            st.error("Please enter recipient email")
                        else:
                            success, message = send_ticket_email(recipient_email, recipient_name, ticket_number, sponsor['company_name'])
                            if success:
                                update_ticket_email(ticket_id, recipient_email, recipient_name)
                                st.success(f"Email sent to {recipient_email}! Please have the recipient check their Spam/Junk folder if the email doesn't arrive in their inbox.")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"Failed to send email: {message}")
                
                printable_html = generate_printable_html_file(ticket_number, name, sponsor['company_name'])
                st.download_button(
                    label="Download & Print Ticket",
                    data=printable_html,
                    file_name=f"ticket_{ticket_number}.html",
                    mime="text/html",
                    help="Download this file and open it - it will automatically open the print dialog",
                    key=f"download_{ticket_id}"
                )
            
            st.markdown("### Print Preview")
            st.markdown(generate_printable_ticket(ticket_number, name, sponsor['company_name']), unsafe_allow_html=True)
