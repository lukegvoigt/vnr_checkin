import os
import psycopg2
import csv

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
    SELECT prefix, first_name, last_name, suffix, school_system, grade_subject, 
           bringing_plus_one, email, status, school_cleaned, qr_code, 
           attendance_response, checked_in, toty
    FROM attendees
""")

rows = cur.fetchall()
columns = ['prefix', 'first_name', 'last_name', 'suffix', 'school_system', 'grade_subject',
           'bringing_plus_one', 'email', 'status', 'school_cleaned', 'qr_code',
           'attendance_response', 'checked_in', 'toty']

with open('attendees_backup_2025.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

print(f"Backup complete! Saved {len(rows)} records to attendees_backup_2025.csv")

cur.close()
conn.close()
