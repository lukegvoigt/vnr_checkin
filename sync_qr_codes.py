
import os
import psycopg2
import pandas as pd

def sync_qr_codes():
    try:
        # Read CSV file
        df = pd.read_csv('tad.csv')
        
        # Connect to database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # Get existing QR codes from database
        cur.execute("SELECT qr_code FROM attendees")
        existing_qr_codes = {row[0] for row in cur.fetchall()}
        
        # Find new entries
        for _, row in df.iterrows():
            if str(row['qr_code']) not in existing_qr_codes:
                # Insert new record
                # Convert bringing_plus_one to proper boolean
                plus_one = False
                if pd.notna(row['bringing_plus_one']):
                    plus_one = str(row['bringing_plus_one']).lower() == 'yes'

                cur.execute("""
                    INSERT INTO attendees (
                        prefix, first_name, last_name, suffix,
                        school_system, grade_subject, bringing_plus_one,
                        email, status, school_cleaned, qr_code,
                        attendance_response, checked_in
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '0')
                """, (
                    row['prefix'],
                    row['first_name'],
                    row['last_name'],
                    row['suffix'],
                    row['school_system'],
                    row['grade_subject'],
                    plus_one,
                    row['email'],
                    row['status'],
                    row['school_cleaned'],
                    str(row['qr_code']),
                    row['attendance_response']
                ))
                print(f"Added new entry for {row['first_name']} {row['last_name']}")
        
        conn.commit()
        print("Database sync completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    sync_qr_codes()
