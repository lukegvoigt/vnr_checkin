import os
import psycopg2
import pandas as pd

def get_table_info():
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()

        # Fetching the table names
        cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
        """)

        tables = cur.fetchall()
        for table in tables:
            table_name = table[0]
            print(f"Table: {table_name}")

            # Fetching column names for the current table
            cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}';
            """)
            columns = [col[0] for col in cur.fetchall()]
            print("Columns:", columns)
            print()  # New line for better readability

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_csv_headers():
    try:
        # Read the CSV file
        df = pd.read_csv('tad.csv')

        # Get and print the column headers
        headers = df.columns.tolist()
        print("CSV Headers:")
        for header in headers:
            print(f"- {header}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    get_table_info()
    get_csv_headers()