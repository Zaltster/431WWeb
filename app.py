from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
import sqlite3
import csv
import hashlib
import re

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'nittany_business_secret_key'  # Change in production
app.config['DATABASE'] = 'database.db'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Helper Function - Connect to Database
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Start Database
def init_db():
    with open('schema.sql', 'r') as f:
        schema = f.read()

    conn = get_db_connection()
    conn.executescript(schema)
    conn.close()
    print("Database schema initialized.")

# Import Users from the given CSV file - uses SHA-256 hashing to encrypt passwords
def import_users_from_csv(csv_file):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if User table exist
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
                password_hash = hashlib.sha256(row['password'].encode('utf-8')).hexdigest()

                # Add a user into Table
                cursor.execute(
                    "INSERT OR REPLACE INTO Users (email, password) VALUES (?, ?)",
                    (row['email'], password_hash)
                )

                # Insert into respective sub class Table based on user type
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

# Index/Home Routing
@app.route('/')
def index():
    return render_template('index.html')

# Login routing
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = 'remember' in request.form

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
        
        # Set a longer session lifetime if "remember me" is checked
        if remember:
            session.permanent = True

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

# Signup Routing
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("Signup route accessed")  # Debug print
    
    if request.method == 'POST':
        try:
            print("Processing signup POST request")  # Debug print
            print(f"Form data: {request.form}")  # Debug print
            
            # Extract form data
            email = request.form['email']
            password = request.form['password']
            user_type = request.form['user_type']
            
            print(f"Signup attempt - Email: {email}, Type: {user_type}")  # Debug print
            
            # Check if email already exists
            conn = get_db_connection()
            existing_user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
            
            if existing_user:
                print(f"Email {email} already exists in database")  # Debug print
                conn.close()
                error = "Email already registered. Please use a different email or login."
                return render_template('signup.html', error=error)
            
            # Hash the password using SHA-256 (for consistency with existing code)
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            print(f"Password hashed: {password_hash[:20]}...")  # Debug print - only show part of hash
            
            # Insert the new user
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Users (email, password) VALUES (?, ?)', (email, password_hash))
            print(f"User added to Users table: {email}")  # Debug print
            
            # Handle user-specific data based on type
            if user_type == 'buyer':
                business_name = request.form.get('business_name', '')
                
                # Handle address creation first
                street_num = request.form.get('street_num', '')
                street_name = request.form.get('street_name', '')
                zipcode = request.form.get('zipcode', '')
                
                # Check if zipcode exists, if not add it
                address_id = None
                if zipcode:
                    zip_exists = conn.execute('SELECT * FROM Zipcode_Info WHERE zipcode = ?', (zipcode,)).fetchone()
                    if not zip_exists:
                        city = request.form.get('city', '')
                        state = request.form.get('state', '')
                        print(f"Adding new zipcode: {zipcode}, {city}, {state}")  # Debug print
                        cursor.execute('INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)', 
                                    (zipcode, city, state))
                
                # Create address record
                if street_num and street_name and zipcode:
                    print(f"Creating address record: {street_num} {street_name}, {zipcode}")  # Debug print
                    cursor.execute('''
                        INSERT INTO Address (zipcode, street_num, street_name) 
                        VALUES (?, ?, ?)
                    ''', (zipcode, street_num, street_name))
                    address_id = cursor.lastrowid
                    print(f"Created address with ID: {address_id}")  # Debug print
                
                # Create buyer record
                print(f"Creating buyer record: {email}, {business_name}, {address_id}")  # Debug print
                cursor.execute('''
                    INSERT INTO Buyer (email, business_name, buyer_address_id) 
                    VALUES (?, ?, ?)
                ''', (email, business_name, address_id))
                
                # Handle credit card info if provided
                card_num = request.form.get('credit_card_num', '')
                if card_num:
                    card_type = request.form.get('card_type', '')
                    expire_month = request.form.get('expire_month', '')
                    expire_year = request.form.get('expire_year', '')
                    security_code = request.form.get('security_code', '')
                    
                    print(f"Adding credit card for {email}")  # Debug print
                    cursor.execute('''
                        INSERT INTO Credit_Cards (credit_card_num, card_type, expire_month, 
                        expire_year, security_code, Owner_email) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (card_num, card_type, expire_month, expire_year, security_code, email))
                
            elif user_type == 'seller':
                business_name = request.form.get('seller_business_name', '')
                
                # Handle address creation first
                street_num = request.form.get('seller_street_num', '')
                street_name = request.form.get('seller_street_name', '')
                zipcode = request.form.get('seller_zipcode', '')
                
                # Check if zipcode exists, if not add it
                address_id = None
                if zipcode:
                    zip_exists = conn.execute('SELECT * FROM Zipcode_Info WHERE zipcode = ?', (zipcode,)).fetchone()
                    if not zip_exists:
                        city = request.form.get('seller_city', '')
                        state = request.form.get('seller_state', '')
                        print(f"Adding new zipcode: {zipcode}, {city}, {state}")  # Debug print
                        cursor.execute('INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)', 
                                    (zipcode, city, state))
                
                # Create address record
                if street_num and street_name and zipcode:
                    print(f"Creating address record: {street_num} {street_name}, {zipcode}")  # Debug print
                    cursor.execute('''
                        INSERT INTO Address (zipcode, street_num, street_name) 
                        VALUES (?, ?, ?)
                    ''', (zipcode, street_num, street_name))
                    address_id = cursor.lastrowid
                    print(f"Created address with ID: {address_id}")  # Debug print
                
                # Get banking info
                bank_routing_number = request.form.get('bank_routing_number', '')
                bank_account_number = request.form.get('bank_account_number', '')
                
                # Create seller record with initial balance of 0
                print(f"Creating seller record: {email}, {business_name}, {address_id}")  # Debug print
                cursor.execute('''
                    INSERT INTO Sellers (email, business_name, business_address_id, 
                    bank_routing_number, bank_account_number, balance) 
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (email, business_name, address_id, bank_routing_number, bank_account_number))
                
            elif user_type == 'helpdesk':
                position = request.form.get('position', 'Support Staff')
                
                # Create helpdesk record
                print(f"Creating helpdesk record: {email}, {position}")  # Debug print
                cursor.execute('INSERT INTO Helpdesk (email, position) VALUES (?, ?)', 
                             (email, position))
            
            # Commit the transaction
            conn.commit()
            print(f"Successfully created account for {email} as {user_type}")  # Debug print
            conn.close()
            
            # Set session data
            session['user_email'] = email
            session['user_type'] = user_type
            
            print(f"Setting session for {email} as {user_type}")  # Debug print
            
            # Redirect to appropriate dashboard
            if user_type == 'buyer':
                return redirect(url_for('buyer_dashboard'))
            elif user_type == 'seller':
                return redirect(url_for('seller_dashboard'))
            elif user_type == 'helpdesk':
                return redirect(url_for('helpdesk_dashboard'))
            else:
                return redirect(url_for('dashboard'))
                
        except Exception as e:
            print(f"Error during signup: {str(e)}")  # Debug print
            conn.rollback()
            conn.close()
            error = f"An error occurred during signup: {str(e)}"
            return render_template('signup.html', error=error)
    
    # For GET request, show the signup form
    # If a user type was specified in the query string, pre-select that option
    user_type = request.args.get('type', 'buyer')
    print(f"Showing signup form with preselected type: {user_type}")  # Debug print
    return render_template('signup.html', selected_type=user_type)

# Forgot Password Route
@app.route('/forgot-password')
def forgot_password():
    # This would typically email a reset link
    # For now, we'll just provide a placeholder page
    return render_template('forgot_password.html')

# Dashboard routing
@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type=session['user_type'])

# Dashboard routing for helpdesk
@app.route('/helpdesk_dashboard')
def helpdesk_dashboard():
    if 'user_email' not in session or session['user_type'] != 'helpdesk':
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type='helpdesk')

# Dashboard routing for buyer
@app.route('/buyer_dashboard')
def buyer_dashboard():
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type='buyer')

# Dashboard routing for seller
@app.route('/seller_dashboard')
def seller_dashboard():
    if 'user_email' not in session or session['user_type'] != 'seller':
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_email=session['user_email'], user_type='seller')

# Logout routing
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)