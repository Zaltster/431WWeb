import sqlite3
import csv


def populate_address_table():
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    print("Creating Address table if it doesn't exist...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Address (
        address_ID TEXT PRIMARY KEY,
        zipcode TEXT NOT NULL,
        street_num INTEGER NOT NULL,
        street_name TEXT NOT NULL,
        FOREIGN KEY (zipcode) REFERENCES Zipcode_Info(zipcode)
    )
    ''')
    conn.commit()

    # Temporarily disable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = OFF")
    conn.commit()

    try:
        # Open and read the CSV file
        print("Opening Address.csv file...")
        with open('Address.csv', 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row

            insert_count = 0
            print("Processing addresses...")
            for row in reader:
                if len(row) >= 4:  # Ensure we have all required columns
                    address_id = row[0].strip()
                    zipcode = row[1].strip()
                    street_num = row[2].strip()
                    street_name = row[3].strip()

                    if address_id and zipcode and street_name:
                        try:
                            cursor.execute(
                                "INSERT OR REPLACE INTO Address (address_ID, zipcode, street_num, street_name) VALUES (?, ?, ?, ?)",
                                (address_id, zipcode, int(street_num), street_name)
                            )
                            insert_count += 1
                        except Exception as e:
                            print(f"Error with address {address_id}: {str(e)}")

            conn.commit()
            print(f"Successfully added {insert_count} addresses.")

            # Show sample of imported addresses
            cursor.execute(
                "SELECT address_ID, zipcode, street_num, street_name FROM Address LIMIT 5")
            addresses = cursor.fetchall()
            print("\nSample of imported addresses:")
            for address in addresses:
                print(
                    f"ID: {address[0]}, Zipcode: {address[1]}, Street: {address[2]} {address[3]}")

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
    print("Starting address import process...")
    populate_address_table()
    print("Process completed.")
