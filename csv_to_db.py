import csv
import psycopg2
import os
import requests
from io import StringIO  # For handling string as file

def csv_url_to_postgres(csv_url, table_name):
    """
    Downloads a CSV file from a URL, reads data, and inserts it into a PostgreSQL table.
    Database connection details are read from environment variables.

    Args:
        csv_url (str): URL of the CSV file.
        table_name (str): Name of the PostgreSQL table to insert into.
    """

    conn = None  # Initialize conn to None for proper error handling
    cur = None   # Initialize cur to None for proper error handling

    try:
        # --- Database Connection from Environment Variables ---
        db_url = os.environ.get('DATABASE_URL')

        if db_url:
            # Use DATABASE_URL if available (e.g., for Heroku, Render)
            conn = psycopg2.connect(db_url)
        else:
            # Fallback to individual PG* environment variables
            dbname = os.environ.get('PGDATABASE')
            host = os.environ.get('PGHOST')
            port = os.environ.get('PGPORT', '5432')  # Default port if PGPORT is not set
            user = os.environ.get('PGUSER')
            password = os.environ.get('PGPASSWORD')

            if not all([dbname, host, user, password]):
                raise ValueError("Database connection details not fully configured. "
                                 "Set either DATABASE_URL or PGDATABASE, PGHOST, PGPORT, PGUSER, PGPASSWORD environment variables.")

            conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)

        cur = conn.cursor()

        # --- Fetch CSV content from URL ---
        response = requests.get(csv_url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        csv_text = response.text  # Get text content of the CSV

        csvfile = StringIO(csv_text) # Treat the string as a file
        csv_reader = csv.reader(csvfile)
        header = next(csv_reader)  # Assume first row is header

        # Construct the INSERT SQL statement (assuming CSV column order matches table column order)
        placeholders = ', '.join(['%s'] * len(header))
        columns = ', '.join([col.lower().replace(' ', '_').replace('(optional):', '').replace('(e.g._jr.,_iii)', '').replace('(this_is_only_to_send_updates_about_this_event._if_you_are_allocated_a_seat,_you_will_receive_a_confirmation_email_with_a_barcode_and_event_id.)', '').replace('/', '_').replace('?', '').replace('.', '') for col in header]) # Sanitize headers for db columns
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        for row in csv_reader:
            try:
                # Execute the INSERT statement for each row
                cur.execute(sql, row)
            except Exception as e_insert:
                print(f"Error inserting row: {row} - Error: {e_insert}")
                conn.rollback()  # Rollback the current transaction
                continue # Skip to the next row

        conn.commit()  # Commit all successful insertions
        print(f"Successfully imported data from CSV URL '{csv_url}' to table '{table_name}' in PostgreSQL.")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except requests.exceptions.RequestException as e_request:
        print(f"Error fetching CSV from URL '{csv_url}': {e_request}")
    except psycopg2.Error as e_conn:
        print(f"Error connecting to PostgreSQL: {e_conn}")
    except Exception as e_general:
        print(f"An unexpected error occurred: {e_general}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    # --- Configuration ---
    CSV_URL = '/attendees.csv'  # <-- Replace with the URL of your CSV file
    TABLE_NAME = 'teacher_dinner_attendees'  # <-- Replace with your PostgreSQL table name

    # --- Database connection details are expected to be in environment variables ---
    # DATABASE_URL or (PGDATABASE, PGHOST, PGPORT, PGUSER, PGPASSWORD)

    # --- Run the CSV URL to PostgreSQL import ---
    csv_url_to_postgres(CSV_URL, TABLE_NAME)