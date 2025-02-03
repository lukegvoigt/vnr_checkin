
import os
import psycopg2

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Add toty column
    cur.execute("""
        ALTER TABLE attendees 
        ADD COLUMN IF NOT EXISTS toty INTEGER DEFAULT 0;
    """)
    
    # Update toty values for rows where plus_one is true
    cur.execute("""
        UPDATE attendees 
        SET toty = 1 
        WHERE bringing_plus_one = true;
    """)
    
    # Update superintendents to toty=3
    cur.execute("""
        UPDATE attendees 
        SET toty = 3 
        WHERE email IN ('sandrawilcher@lowndes.k12.ga.us', 'clockhart@gocats.org');
    """)
    
    conn.commit()
    print("Successfully added and updated toty column and superintendent values")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
