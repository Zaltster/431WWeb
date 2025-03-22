from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import csv
import os

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'nittany_business_secret_key'  # Change in production
app.config['DATABASE'] = 'database.db'

# Database connection helper


def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database schema


def init_db():
    with open('schema.sql', 'r') as f:
        schema = f.read()

    conn = get_db_connection()
    conn.executescript(schema)
    conn.close()
    print("Database schema initialized.")

# Import users from CSV with password hashing


def import_users_from_csv(csv_file):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if Users table exists and has data
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Users'")
    if cursor.fetchone() is None:
        print("Users table does not exist. Initialize the database first.")
        conn.close()
        return

    # Read users from CSV
    try:
        with open(csv_file, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Hash the password before storing
                password_hash = generate_password_hash(
                    row['password'], method='sha256')

                # Insert into Users table
                cursor.execute(
                    "INSERT OR REPLACE INTO Users (email, password) VALUES (?, ?)",
                    (row['email'], password_hash)
                )

                # Handle different user types based on email
                if 'helpdesk' in row['email']:
                    cursor.execute(
                        "INSERT OR REPLACE INTO Helpdesk (email, position) VALUES (?, ?)",
                        (row['email'], row.get('position', 'Support Staff'))
                    )
                elif 'buyer' in row['email']:
                    cursor.execute(
                        "INSERT OR REPLACE INTO Buyer (email, business_name, buyer_address_id) VALUES (?, ?, ?)",
                        (row['email'], row.get('business_name', 'Business'),
                         row.get('buyer_address_id', None))
                    )
                elif 'seller' in row['email']:
                    cursor.execute(
                        "INSERT OR REPLACE INTO Sellers (email, business_name, business_address_id, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?, ?, ?)",
                        (row['email'], row.get('business_name', 'Business'), row.get('business_address_id', None),
                         row.get('bank_routing_number', None), row.get('bank_account_number', None), row.get('balance', 0))
                    )

        conn.commit()
        print("Users imported successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error importing users: {e}")
    finally:
        conn.close()

# Routes


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print(f"Login attempt for email: {email}")  # Debug print

        # Validate user credentials
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM Users WHERE email = ?', (email,)).fetchone()

        # Debug prints
        if user:
            print(f"User found in database: {user['email']}")
            # Show first part of hash
            print(f"Password hash in DB: {user['password'][:20]}...")
        else:
            print(f"No user found with email: {email}")

        conn.close()

        if user is None:
            error = "Invalid email address."
            print(f"Login failed: {error}")  # Debug print
            return render_template('login.html', error=error)

        # Calculate SHA-256 hash of the provided password for comparison
        import hashlib
        provided_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        stored_hash = user['password']

        print(f"Comparing hashes:")
        print(f"Stored:   {stored_hash[:20]}...")
        print(f"Provided: {provided_hash[:20]}...")

        # Verify the password using direct comparison of SHA-256 hashes
        if provided_hash != stored_hash:
            error = "Invalid password."
            print(f"Login failed: {error}")  # Debug print
            return render_template('login.html', error=error)

        # Login successful - store user info in session
        print(f"Login successful for {email}")  # Debug print
        session['user_email'] = user['email']

        # Determine user type based on email
        if 'helpdesk' in email:
            session['user_type'] = 'helpdesk'
            print(f"Redirecting to helpdesk_dashboard")  # Debug print
            return redirect(url_for('helpdesk_dashboard'))
        elif 'buyer' in email:
            session['user_type'] = 'buyer'
            print(f"Redirecting to buyer_dashboard")  # Debug print
            return redirect(url_for('buyer_dashboard'))
        elif 'seller' in email:
            session['user_type'] = 'seller'
            print(f"Redirecting to seller_dashboard")  # Debug print
            return redirect(url_for('seller_dashboard'))
        else:
            session['user_type'] = 'user'
            print(f"Redirecting to dashboard")  # Debug print
            return redirect(url_for('dashboard'))

    # GET request - show login page
    return render_template('login.html', error=error)


@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type=session['user_type'])


@app.route('/helpdesk_dashboard')
def helpdesk_dashboard():
    if 'user_email' not in session or session['user_type'] != 'helpdesk':
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type='helpdesk')


@app.route('/buyer_dashboard')
def buyer_dashboard():
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type='buyer')


@app.route('/seller_dashboard')
def seller_dashboard():
    if 'user_email' not in session or session['user_type'] != 'seller':
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type='seller')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
