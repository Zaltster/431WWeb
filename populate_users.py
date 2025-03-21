import sqlite3
import csv
import hashlib


def hash_password(password):
    """Simple SHA-256 hashing function"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def populate_users_table():
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    print("Creating Users table if it doesn't exist...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        email TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()

    try:
        # Open and read the CSV file
        print("Opening Users.csv file...")
        with open('Users.csv', 'r', encoding='utf-8-sig') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row

            insert_count = 0
            print("Processing users...")
            for row in reader:
                if len(row) >= 2:
                    email = row[0].strip()
                    password = row[1].strip()

                    if email and password:
                        # Hash the password with SHA-256
                        hashed_password = hash_password(password)

                        # Insert user with hashed password
                        cursor.execute(
                            "INSERT OR REPLACE INTO Users (email, password) VALUES (?, ?)",
                            (email, hashed_password)
                        )
                        insert_count += 1

            conn.commit()
            print(
                f"Successfully added {insert_count} users with hashed passwords.")

            # Show sample of imported users
            cursor.execute("SELECT email, password FROM Users LIMIT 5")
            users = cursor.fetchall()
            print("\nSample of imported users:")
            for user in users:
                print(f"Email: {user[0]}, Password hash: {user[1][:10]}...")

    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    print("Starting user import process...")
    populate_users_table()
    print("Process completed.")
