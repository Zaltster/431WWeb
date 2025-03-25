import sqlite3
import csv


def populate_requests_table():
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    print("Creating Requests table if it doesn't exist...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Requests (
        request_id INTEGER PRIMARY KEY,
        sender_email TEXT NOT NULL,
        helpdesk_staff_email TEXT NOT NULL,
        request_type TEXT NOT NULL,
        request_desc TEXT,
        request_status INTEGER
    )
    ''')
    conn.commit()

    # Temporarily disable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = OFF")
    conn.commit()

    try:
        # Open and read the CSV file
        print("Opening Requests.csv file...")
        with open('Requests.csv', 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row

            insert_count = 0
            print("Processing requests...")
            for row in reader:
                if len(row) >= 6:  # Ensure we have all required columns
                    request_id = row[0].strip()
                    sender_email = row[1].strip()
                    helpdesk_staff_email = row[2].strip()
                    request_type = row[3].strip()
                    request_desc = row[4].strip()
                    request_status = row[5].strip()

                    if request_id and sender_email and helpdesk_staff_email:
                        try:
                            cursor.execute(
                                "INSERT OR REPLACE INTO Requests (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) VALUES (?, ?, ?, ?, ?, ?)",
                                (int(request_id), sender_email, helpdesk_staff_email,
                                 request_type, request_desc, int(request_status))
                            )
                            insert_count += 1
                        except Exception as e:
                            print(f"Error with request {request_id}: {str(e)}")

            conn.commit()
            print(f"Successfully added {insert_count} requests.")

            # Show sample of imported requests
            cursor.execute(
                "SELECT request_id, sender_email, request_type, request_status FROM Requests LIMIT 5")
            requests = cursor.fetchall()
            print("\nSample of imported requests:")
            for request in requests:
                print(
                    f"ID: {request[0]}, Sender: {request[1]}, Type: {request[2]}, Status: {request[3]}")

    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    print("Starting requests import process...")
    populate_requests_table()
    print("Process completed.")
