
import csv
import random

def generate_qr_code():
    return str(random.randint(10000, 99999))

new_entries = [
    {
        'prefix': '',
        'first_name': 'Kaylie',
        'last_name': 'Willis',
        'suffix': '',
        'school_system': 'Lowndes County Schools',
        'grade_subject': '',
        'bringing_plus_one': '',
        'email': 'kayliewillis@lowndes.k12.ga.us',
        'status': 'Invited',
        'school_cleaned': '',
        'qr_code': generate_qr_code(),
        'attendance_response': '',
        'year': 2026
    },
    {
        'prefix': '',
        'first_name': 'Tenry',
        'last_name': 'Berry',
        'suffix': '',
        'school_system': 'Lowndes County Schools',
        'grade_subject': '',
        'bringing_plus_one': '',
        'email': 'tenryberry@lowndes.k12.ga.us',
        'status': 'Invited',
        'school_cleaned': '',
        'qr_code': generate_qr_code(),
        'attendance_response': '',
        'year': 2026
    },
    {
        'prefix': '',
        'first_name': 'Amber',
        'last_name': 'Hiers',
        'suffix': '',
        'school_system': 'Lowndes County Schools',
        'grade_subject': '',
        'bringing_plus_one': '',
        'email': 'amberhiers@lowndes.k12.ga.us',
        'status': 'Invited',
        'school_cleaned': '',
        'qr_code': generate_qr_code(),
        'attendance_response': '',
        'year': 2026
    },
    {
        'prefix': '',
        'first_name': 'Porchia',
        'last_name': 'Seawright',
        'suffix': '',
        'school_system': 'Lowndes County Schools',
        'grade_subject': '',
        'bringing_plus_one': '',
        'email': 'porchiaseawright@lowndes.k12.ga.us',
        'status': 'Invited',
        'school_cleaned': '',
        'qr_code': generate_qr_code(),
        'attendance_response': '',
        'year': 2026
    }
]

# Append new entries to the CSV file
with open('tad.csv', 'a', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=[
        'prefix', 'first_name', 'last_name', 'suffix', 'school_system',
        'grade_subject', 'bringing_plus_one', 'email', 'status',
        'school_cleaned', 'qr_code', 'attendance_response', 'year'
    ])
    
    for entry in new_entries:
        writer.writerow(entry)

print("New entries have been added to tad.csv")
