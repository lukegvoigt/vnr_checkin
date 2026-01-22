
import os
import psycopg2
import pandas as pd

def create_attendees_table():
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # Create attendees table
        cur.execute("""
        DROP TABLE IF EXISTS attendees;
        CREATE TABLE attendees (
            prefix TEXT,
            first_name TEXT,
            last_name TEXT,
            suffix TEXT,
            school_system TEXT,
            grade_subject TEXT,
            bringing_plus_one BOOLEAN,
            email TEXT,
            status TEXT,
            school_cleaned TEXT,
            qr_code TEXT,
            attendance_response TEXT,
            checked_in INTEGER DEFAULT 0,
            year INTEGER DEFAULT 2026
        );
        """)
        
        # Read CSV and insert data
        df = pd.read_csv('tad.csv')
        
        # Insert data into the database
        for _, row in df.iterrows():
            year_value = row.get('year', 2026)
            cur.execute("""
            INSERT INTO attendees (
                prefix, first_name, last_name, suffix, 
                school_system, grade_subject, bringing_plus_one,
                email, status, school_cleaned, qr_code,
                attendance_response, year
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['prefix'],
                row['first_name'],
                row['last_name'],
                row['suffix'],
                row['school_system'],
                row['grade_subject'],
                row['bringing_plus_one'] == 'Yes',
                row['email'],
                row['status'],
                row['school_cleaned'],
                row['qr_code'],
                row['attendance_response'],
                year_value
            ))
        
        conn.commit()
        print("Table created and data imported successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_table_info():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # Get column information for attendees table
        cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'attendees';
        """)
        
        print("\nTable Structure:")
        for column in cur.fetchall():
            print(f"- {column[0]}: {column[1]}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



def reset_check_ins():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()
        
        # Reset both checked_in and status columns
        cur.execute("""
        UPDATE attendees 
        SET checked_in = 0, 
            status = 'Not Checked In'
        """)
        
        conn.commit()
        print("Successfully reset all check-in statuses!")
        
    except Exception as e:
        print(f"An error occurred while resetting check-ins: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



if __name__ == "__main__":
    user_input = input("Enter 1 to get table info, 2 to create attendees table, 6 to reset check-ins: ")
    if user_input == '1':
        get_table_info()
    elif user_input == '2':
        create_attendees_table()
    elif user_input == '6':
        reset_check_ins()
