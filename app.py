from flask import Flask, render_template, request, flash, redirect
import sqlite3 as sql

# Initialize the Flask application
app = Flask(__name__)

# Secret key is required for flash messages
app.secret_key = 'your_secret_key_here'

# ------------------------ HOME PAGE ------------------------

@app.route('/')
def index():
    """
    Renders the main index page.
    This page will have options to add or delete patients.
    """
    return render_template('index.html')

# ------------------------ ADD PATIENT PAGE ------------------------

@app.route('/name', methods=['POST', 'GET'])
def name():
    """
    Handles patient form submission and displays all stored patients.
    - If the request is GET, it fetches and displays all patients.
    - If the request is POST, it adds a new patient and refreshes the page.
    """
    error = None
    result = fetch_all_patients()  # Fetch existing patients to display

    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']

        if first_name and last_name:
            insert_patient(first_name, last_name)  # Insert into DB
            flash('Patient added successfully!', 'success')  # Show success message
            return redirect('/name')  # Redirect to avoid form resubmission
        else:
            error = 'Invalid input name'

    return render_template('input.html', error=error, result=result)

# ------------------------ DELETE PATIENT PAGE ------------------------

@app.route('/delete', methods=['POST', 'GET'])
def delete():
    """
    Handles patient deletion and displays the updated patient list.
    - If the request is GET, it shows all patients.
    - If the request is POST, it deletes a patient and refreshes the page.
    """
    result = fetch_all_patients()  # Fetch patients to display

    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        
        if first_name and last_name:
            success = delete_patient(first_name, last_name)  # Delete patient
            if success:
                flash(f'Patient {first_name} {last_name} deleted successfully!', 'success')
            else:
                flash(f'Patient {first_name} {last_name} not found.', 'danger')

            return redirect('/delete')  # Redirect to avoid form resubmission

    return render_template('delete.html', result=result)

# ------------------------ DATABASE OPERATIONS ------------------------

def insert_patient(first_name, last_name):
    """
    Inserts a new patient with a unique PID into the database.
    - `pid` is auto-incremented for each new entry.
    - First and last names are capitalized for consistency.
    """
    first_name = first_name.capitalize()
    last_name = last_name.capitalize()

    connection = sql.connect('database.db')  # Connect to the database
    cursor = connection.cursor()
    
    # Ensure the table exists before inserting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            pid INTEGER PRIMARY KEY AUTOINCREMENT, 
            firstname TEXT, 
            lastname TEXT
        );
    ''')

    # Insert the new patient
    cursor.execute('INSERT INTO patients (firstname, lastname) VALUES (?, ?);', (first_name, last_name))
    
    connection.commit()  # Save changes
    connection.close()  # Close the database connection

def fetch_all_patients():
    """
    Retrieves all stored patients from the database.
    Returns a list of tuples (pid, first_name, last_name).
    """
    connection = sql.connect('database.db')  # Connect to the database
    cursor = connection.cursor()

    # Ensure table exists before fetching data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            pid INTEGER PRIMARY KEY AUTOINCREMENT, 
            firstname TEXT, 
            lastname TEXT
        );
    ''')

    cursor.execute('SELECT * FROM patients;')  # Retrieve all patient records
    result = cursor.fetchall()

    connection.close()  # Close the database connection
    return result

def delete_patient(first_name, last_name):
    """
    Deletes a patient from the database if they exist.
    Returns True if deleted successfully, False if the patient was not found.
    """
    connection = sql.connect('database.db')  # Connect to the database
    cursor = connection.cursor()

    # Check if the patient exists
    cursor.execute('SELECT * FROM patients WHERE firstname = ? AND lastname = ?', (first_name, last_name))
    patient = cursor.fetchone()

    if patient:
        # Delete the patient if found
        cursor.execute('DELETE FROM patients WHERE firstname = ? AND lastname = ?', (first_name, last_name))
        connection.commit()  # Save changes
        connection.close()
        return True

    connection.close()
    return False  # Return False if patient not found

# ------------------------ RUN FLASK APP ------------------------

if __name__ == "__main__":
    app.run()
