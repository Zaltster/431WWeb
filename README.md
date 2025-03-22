# NittanyBusiness Project - Phase 2 Progress Review

## Project Overview

This is a Flask-based web application for the NittanyBusiness system, focusing on the User Login functionality for the Phase 2 Progress Review. The system implements secure user authentication with password hashing to meet the project requirements.

## Features

- User authentication system with secure password hashing using SHA-256
- Role-based access control (Buyer, Seller, Helpdesk)
- Session management for authenticated users
- Error handling for invalid login attempts
- Comprehensive database schema for business operations

## Project Structure

```
431WWeb/
├── templates/              # HTML templates directory
│   ├── dashboard.html      # Dashboard page after successful login
│   ├── index.html          # Home/landing page
│   └── login.html          # Login page with error handling
├── app.py                  # Main Flask application
├── schema.sql              # Database schema definition
├── database.db             # SQLite database
├── Users.csv               # User data for import
├── Helpdesk.csv            # Helpdesk staff data
├── Sellers.csv             # Sellers data
├── Buyers.csv              # Buyers data
├── Orders.csv              # Orders data
├── Reviews.csv             # Reviews data
├── Product_Listings.csv    # Product listings data
├── Categories.csv          # Categories data
├── Address.csv             # Address data
├── Zipcode_Info.csv        # Zipcode information
├── Credit_Cards.csv        # Credit card data
└── Requests.csv            # Support requests data
```

## Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **Authentication**: SHA-256 password hashing
- **Frontend**: HTML

## Setup Instructions

### Prerequisites

- Python 3.6 or higher
- Flask
- SQLite3

### Installation

1. Clone the repository or extract the project files to your desired location.

2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install required packages:
   ```bash
   pip install flask werkzeug
   ```

### Database Setup

Several scripts are provided to populate the database from CSV files:

1. Initialize the database and import users:

   ```bash
   python import_users.py
   ```

2. Import other data as needed:
   ```bash
   python import_helpdesk.py
   python import_sellers.py
   python import_buyers.py
   # Additional import scripts...
   ```

### Running the Application

1. Start the Flask application:

   ```bash
   python app.py
   ```

2. Open your web browser and navigate to `http://127.0.0.1:5000/`

3. Use the login page to authenticate with credentials from the Users.csv file.

## Usage

1. From the home page, click "Go to Login Page"
2. Enter a valid email and password from the Users.csv file
3. Upon successful authentication, you'll be redirected to a dashboard based on your user type (Buyer, Seller, or Helpdesk)
4. Use the logout link to end your session

## Security Features

- Passwords are hashed using SHA-256 before storage
- Passwords are not visible during entry (type="password")
- Session-based authentication
- Error messages do not reveal sensitive information

## Project Authors

- 2D2S, The greats
