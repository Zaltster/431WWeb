from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
import sqlite3
import hashlib
import re

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'nittany_business_secret_key'  
app.config['DATABASE'] = 'database.db'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  #<- around 30 minutes

#=======================Helper=======================#
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn
#=======================Helper=======================#

#=======================LandingPage=======================#
@app.route('/')
def index(): #<- homepage/landing page 
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = 'remember' in request.form
        print(f"Login attempt for email: {email}") 
        # validate user credentials
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
        if user:
            print(f"User found in database: {user['email']}")
            # show first part of hash
            print(f"Password hash in DB: {user['password'][:20]}...")
        else:
            print(f"No user found with email: {email}")
        conn.close()
        if user is None:
            error = "Invalid email address."
            print(f"Login failed: {error}")  
            return render_template('login.html', error=error)
        # calculate SHA-256 hash of the provided password for comparison
        provided_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        stored_hash = user['password']
        print(f"Comparing hashes:")
        print(f"Stored:   {stored_hash[:20]}...")
        print(f"Provided: {provided_hash[:20]}...")
        # verify the password using direct comparison of SHA-256 hashes
        if provided_hash != stored_hash:
            error = "Invalid password."
            print(f"Login failed: {error}")  
            return render_template('login.html', error=error)
        print(f"Login successful for {email}")  
        session['user_email'] = user['email']
        
        # set a longer session lifetime if "remember me" is checked
        if remember:
            session.permanent = True
            
        # determine user type based on database records
        conn = get_db_connection()  # get a fresh connection
        buyer = conn.execute('SELECT * FROM Buyer WHERE email = ?', (email,)).fetchone()
        seller = conn.execute('SELECT * FROM Sellers WHERE email = ?', (email,)).fetchone()
        helpdesk = conn.execute('SELECT * FROM Helpdesk WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if helpdesk:
            session['user_type'] = 'helpdesk'
            print(f"Redirecting to helpdesk_dashboard") 
            return redirect(url_for('helpdesk_dashboard'))
        elif buyer:
            session['user_type'] = 'buyer'
            print(f"Redirecting to buyer_dashboard")  
            return redirect(url_for('buyer_dashboard'))
        elif seller:
            session['user_type'] = 'seller'
            print(f"Redirecting to seller_dashboard") 
            return redirect(url_for('seller_dashboard'))
        else:
            return render_template('login.html', error=error)
    
    #throw error if get or form submission fails 
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("Signup route accessed")  
    
    if request.method == 'POST':
        try:
            print("Processing signup POST request")  
            print(f"Form data: {request.form}")  
            
            #extract form data
            email = request.form['email']
            password = request.form['password']
            user_type = request.form['user_type']
            
            print(f"Signup attempt - Email: {email}, Type: {user_type}")  
            
            #check if email already exists
            conn = get_db_connection()
            existing_user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
            
            if existing_user:
                print(f"Email {email} already exists in database")  
                conn.close()
                error = "Email already registered. Please use a different email or login."
                return render_template('signup.html', error=error)
            
            #hash the password using SHA-256 (for consistency with existing code)
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            print(f"Password hashed: {password_hash[:20]}...")   #<- only show part of hash
            
            # insert the new user
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Users (email, password) VALUES (?, ?)', (email, password_hash))
            print(f"User added to Users table: {email}")  
            
            # handle user-specific data based on type
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
                        print(f"Adding new zipcode: {zipcode}, {city}, {state}")  
                        cursor.execute('INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)', 
                                    (zipcode, city, state))
                
                # Create address record
                if street_num and street_name and zipcode:
                    print(f"Creating address record: {street_num} {street_name}, {zipcode}")  
                    cursor.execute('''
                        INSERT INTO Address (zipcode, street_num, street_name) 
                        VALUES (?, ?, ?)
                    ''', (zipcode, street_num, street_name))
                    address_id = cursor.lastrowid
                    print(f"Created address with ID: {address_id}")  
                
                # Create buyer record
                print(f"Creating buyer record: {email}, {business_name}, {address_id}")  
                cursor.execute('''
                    INSERT INTO Buyer (email, business_name, buyer_address_id) 
                    VALUES (?, ?, ?)
                ''', (email, business_name, address_id))
                
                # Handle credit card info 
                card_num = request.form.get('credit_card_num', '')
                if card_num:
                    card_type = request.form.get('card_type', '')
                    expire_month = request.form.get('expire_month', '')
                    expire_year = request.form.get('expire_year', '')
                    security_code = request.form.get('security_code', '')
                    
                    print(f"Adding credit card for {email}")  
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
                        print(f"Adding new zipcode: {zipcode}, {city}, {state}")  
                        cursor.execute('INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)', 
                                    (zipcode, city, state))
                
                # Create address record
                if street_num and street_name and zipcode:
                    print(f"Creating address record: {street_num} {street_name}, {zipcode}")  
                    cursor.execute('''
                        INSERT INTO Address (zipcode, street_num, street_name) 
                        VALUES (?, ?, ?)
                    ''', (zipcode, street_num, street_name))
                    address_id = cursor.lastrowid
                    print(f"Created address with ID: {address_id}")  
                
                # Get banking info
                bank_routing_number = request.form.get('bank_routing_number', '')
                bank_account_number = request.form.get('bank_account_number', '')
                
                # Create seller record with initial balance of 0
                print(f"Creating seller record: {email}, {business_name}, {address_id}")  
                cursor.execute('''
                    INSERT INTO Sellers (email, business_name, business_address_id, 
                    bank_routing_number, bank_account_number, balance) 
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (email, business_name, address_id, bank_routing_number, bank_account_number))
                
            elif user_type == 'helpdesk':
                position = request.form.get('position', 'Support Staff')
                
                # Create helpdesk record
                print(f"Creating helpdesk record: {email}, {position}")  
                cursor.execute('INSERT INTO Helpdesk (email, position) VALUES (?, ?)', 
                             (email, position))
            
            # Commit the transaction
            conn.commit()
            print(f"Successfully created account for {email} as {user_type}")  
            conn.close()
            
            # Set session data
            session['user_email'] = email
            session['user_type'] = user_type
            
            print(f"Setting session for {email} as {user_type}")  
            
            # Redirect to appropriate dashboard
            if user_type == 'buyer':
                return redirect(url_for('buyer_dashboard'))
            elif user_type == 'seller':
                return redirect(url_for('seller_dashboard'))
            elif user_type == 'helpdesk':
                return redirect(url_for('helpdesk_dashboard'))
                
        except Exception as e:
            print(f"Error during signup: {str(e)}")  
            conn.rollback()
            conn.close()
            error = f"An error occurred during signup: {str(e)}"
            return render_template('signup.html', error=error)
    
    # If a user type was specified in the query string, pre-select that option
    user_type = request.args.get('type', 'buyer')
    print(f"Showing signup form with preselected type: {user_type}")  
    return render_template('signup.html', selected_type=user_type)


#=======================Buyer=======================#
@app.route('/buyer_dashboard')
def buyer_dashboard():
    # Check if user is logged in and is a buyer
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    if session['user_type'] != 'buyer':
        return redirect(url_for('dashboard'))
    
    # Get the current user's information
    conn = get_db_connection()
    
    # Get buyer details
    buyer = conn.execute(
        'SELECT * FROM Buyer WHERE email = ?', 
        (session['user_email'],)
    ).fetchone()
    
    # Get buyer's address
    address = None
    if buyer and buyer['buyer_address_id']:
        address = conn.execute(
            '''SELECT a.*, z.city, z.state 
               FROM Address a 
               JOIN Zipcode_Info z ON a.zipcode = z.zipcode 
               WHERE a.address_id = ?''', 
            (buyer['buyer_address_id'],)
        ).fetchone()
    
    # Get buyer's payment methods
    payment_methods = conn.execute(
        'SELECT * FROM Credit_Cards WHERE Owner_email = ?',
        (session['user_email'],)
    ).fetchall()
    
    # Get order history
    orders = conn.execute(
        '''SELECT o.*, pl.Product_Title, pl.Product_Description, pl.Product_Price,
              (SELECT COUNT(*) FROM Reviews r WHERE r.Order_ID = o.Order_ID) > 0 AS has_review
           FROM Orders o
           JOIN Product_Listings pl ON o.Listing_ID = pl.Listing_ID
           WHERE o.Buyer_Email = ?
           ORDER BY o.Date DESC''',
        (session['user_email'],)
    ).fetchall()
    
    # Get all product categories
    categories = conn.execute(
        'SELECT category_name FROM Categories ORDER BY category_name'
    ).fetchall()
    
    # Get featured products
    featured_products = conn.execute(
        '''SELECT pl.*, s.business_name AS seller_name,
              (SELECT AVG(r.Rating) FROM Reviews r 
               JOIN Orders o ON r.Order_ID = o.Order_ID
               WHERE o.Listing_ID = pl.Listing_ID) AS avg_rating,
              (SELECT COUNT(*) FROM Reviews r 
               JOIN Orders o ON r.Order_ID = o.Order_ID
               WHERE o.Listing_ID = pl.Listing_ID) AS review_count
           FROM Product_Listings pl
           JOIN Sellers s ON pl.Seller_Email = s.email
           WHERE pl.Status = 1
           ORDER BY avg_rating DESC, review_count DESC
           LIMIT 6'''
    ).fetchall()
    
    # Get recent products
    recent_products = conn.execute(
        '''SELECT pl.*, s.business_name AS seller_name,
              (SELECT AVG(r.Rating) FROM Reviews r 
               JOIN Orders o ON r.Order_ID = o.Order_ID
               WHERE o.Listing_ID = pl.Listing_ID) AS avg_rating,
              (SELECT COUNT(*) FROM Reviews r 
               JOIN Orders o ON r.Order_ID = o.Order_ID
               WHERE o.Listing_ID = pl.Listing_ID) AS review_count
           FROM Product_Listings pl
           JOIN Sellers s ON pl.Seller_Email = s.email
           WHERE pl.Status = 1
           ORDER BY pl.Listing_ID DESC
           LIMIT 6'''
    ).fetchall()
    
    conn.close()
    
    # Determine active tab from query parameter or default to 'products'
    active_tab = request.args.get('tab', 'products')
    
    return render_template(
        'buyer_dashboard.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        buyer=buyer,
        address=address,
        payment_methods=payment_methods,
        orders=orders,
        categories=categories,
        featured_products=featured_products,
        recent_products=recent_products,
        active_tab=active_tab
    )

@app.route('/product/<int:listing_id>')
def product_detail(listing_id):
    if 'user_email' not in session:
        flash('Please log in to view product details.', 'warning')
        return redirect(url_for('login'))

    conn = None 
    try:
        conn = get_db_connection() 

        # Get Product Details
        # use join to get  product information along with seller details 
        product = conn.execute(
            '''SELECT pl.*, s.business_name AS seller_name, s.email AS seller_email
               FROM Product_Listings pl
               JOIN Sellers s ON pl.Seller_Email = s.email
               WHERE pl.Listing_ID = ?''',
            (listing_id,)
        ).fetchone()

        # if product is not found
        if not product:
            flash('Product not found.', 'danger')
            return redirect(url_for('buyer_dashboard'))

        # Get Product Reviews 
        # Fetch reviews associated with the product, joining with Orders to get buyer email and order date
        reviews = conn.execute(
            '''SELECT r.*, o.Buyer_Email, o.Date
               FROM Reviews r
               JOIN Orders o ON r.Order_ID = o.Order_ID
               WHERE o.Listing_ID = ?
               ORDER BY o.Date DESC''', #<- Order reviews by date, newest first
            (listing_id,)
        ).fetchall()

        # Calculate Average Rating and Review Count
        rating_data = conn.execute(
            '''SELECT COALESCE(AVG(r.Rating), 0.0) AS average, COUNT(r.Rating) AS count
               FROM Reviews r
               JOIN Orders o ON r.Order_ID = o.Order_ID
               WHERE o.Listing_ID = ?''',
            (listing_id,)
        ).fetchone()

    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        # Redirect to the dashboard
        return redirect(url_for('buyer_dashboard'))
    finally:
        if conn:
            conn.close()

    return render_template(
        'product_detail.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        product=product,
        reviews=reviews,
        # Pass the rating_data object containing 'average' and 'count'
        rating_data=rating_data
    )

@app.route('/product/search')
def product_search():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    # Get search parameters
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    sort_by = request.args.get('sort_by', 'relevance')
    
    print(f"Search parameters: query='{query}', category='{category}', min_price='{min_price}', max_price='{max_price}', sort_by='{sort_by}'")
    
    conn = get_db_connection()
    sql_query = '''
        SELECT pl.*, s.business_name AS seller_name,
            (SELECT AVG(r.Rating) FROM Reviews r 
             JOIN Orders o ON r.Order_ID = o.Order_ID
             WHERE o.Listing_ID = pl.Listing_ID) AS avg_rating,
            (SELECT COUNT(*) FROM Reviews r 
             JOIN Orders o ON r.Order_ID = o.Order_ID
             WHERE o.Listing_ID = pl.Listing_ID) AS review_count
        FROM Product_Listings pl
        JOIN Sellers s ON pl.Seller_Email = s.email
        WHERE pl.Status = 1
    '''
    
    params = []
    
    # Add keyword search
    if query:
        sql_query += ''' AND (
            pl.Product_Title LIKE ? OR 
            pl.Product_Description LIKE ? OR
            s.business_name LIKE ?
        )'''
        query_param = f'%{query}%'
        params.extend([query_param, query_param, query_param])
    
    # Add category filter
    if category:
        sql_query += ' AND pl.Category = ?'
        params.append(category)
    
    # Add price range filter
    if min_price and min_price.isdigit():
        sql_query += ' AND pl.Product_Price >= ?'
        params.append(float(min_price))
    
    if max_price and max_price.isdigit():
        sql_query += ' AND pl.Product_Price <= ?'
        params.append(float(max_price))
    
    # Add sorting
    if sort_by == 'price_low':
        sql_query += ' ORDER BY pl.Product_Price ASC'
    elif sort_by == 'price_high':
        sql_query += ' ORDER BY pl.Product_Price DESC'
    elif sort_by == 'rating':
        sql_query += ' ORDER BY avg_rating DESC NULLS LAST, review_count DESC'
    elif sort_by == 'newest':
        sql_query += ' ORDER BY pl.Listing_ID DESC'
    else:  # Default to relevance
        if query:
            # For relevance, prioritize title matches, then description
            sql_query += ''' ORDER BY 
                CASE WHEN pl.Product_Title LIKE ? THEN 3
                     WHEN pl.Product_Description LIKE ? THEN 2
                     WHEN s.business_name LIKE ? THEN 1
                     ELSE 0
                END DESC'''
            query_param = f'%{query}%'
            params.extend([query_param, query_param, query_param])
        else:
            # If no query, order by rating
            sql_query += ' ORDER BY avg_rating DESC NULLS LAST, review_count DESC'
    
    print("SQL Query:", sql_query)
    print("Params:", params)
    
    try:
        products = conn.execute(sql_query, params).fetchall()
        print(f"Found {len(products)} products.")
    except Exception as e:
        print(f"Error executing query: {e}")
        products = []
    
    # Get all categories for filtering
    categories = conn.execute(
        'SELECT category_name FROM Categories ORDER BY category_name'
    ).fetchall()
    
    conn.close()
    
    # Pass the selected category back to the template
    selected_category = category
    
    return render_template(
        'search_results.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        products=products,
        categories=categories,
        query=query,
        category=selected_category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        result_count=len(products)
    )

@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    
    order_id = request.form.get('order_id')
    rating = request.form.get('rating')
    review_text = request.form.get('review_text')
    
    # Validate inputs
    if not order_id or not rating or not rating.isdigit():
        flash('Invalid review data')
        return redirect(url_for('buyer_dashboard', tab='orders'))
    
    # Check if order exists and belongs to the current user
    conn = get_db_connection()
    order = conn.execute(
        'SELECT * FROM Orders WHERE Order_ID = ? AND Buyer_Email = ?',
        (order_id, session['user_email'])
    ).fetchone()
    
    if not order:
        conn.close()
        flash('Order not found or not authorized')
        return redirect(url_for('buyer_dashboard', tab='orders'))
    
    # Check if review already exists
    existing_review = conn.execute(
        'SELECT * FROM Reviews WHERE Order_ID = ?',
        (order_id,)
    ).fetchone()
    
    if existing_review:
        # Update existing review
        conn.execute(
            'UPDATE Reviews SET Rating = ?, Review_Desc = ? WHERE Order_ID = ?',
            (rating, review_text, order_id)
        )
        flash('Your review has been updated!')
    else:
        # Create new review
        conn.execute(
            'INSERT INTO Reviews (Order_ID, Rating, Review_Desc) VALUES (?, ?, ?)',
            (order_id, rating, review_text)
        )
        flash('Thank you for your review!')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('buyer_dashboard', tab='orders'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    user_type = session['user_type']
    
    # Get form data
    if user_type == 'buyer':
        business_name = request.form.get('business_name', '')
        
        # Address info
        street_num = request.form.get('street_num', '')
        street_name = request.form.get('street_name', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        zipcode = request.form.get('zipcode', '')
        
        # Password change
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        conn = get_db_connection()
        
        # Update business name
        conn.execute(
            'UPDATE Buyer SET business_name = ? WHERE email = ?',
            (business_name, user_email)
        )
        
        # Handle address update
        if street_num and street_name and zipcode:
            # Check if zipcode exists
            zip_exists = conn.execute(
                'SELECT * FROM Zipcode_Info WHERE zipcode = ?', 
                (zipcode,)
            ).fetchone()
            
            if not zip_exists and city and state:
                conn.execute(
                    'INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)',
                    (zipcode, city, state)
                )
            
            # Get current address
            buyer = conn.execute(
                'SELECT * FROM Buyer WHERE email = ?', 
                (user_email,)
            ).fetchone()
            
            if buyer and buyer['buyer_address_id']:
                # Update existing address
                conn.execute(
                    'UPDATE Address SET zipcode = ?, street_num = ?, street_name = ? WHERE address_id = ?',
                    (zipcode, street_num, street_name, buyer['buyer_address_id'])
                )
            else:
                # Create new address
                conn.execute(
                    'INSERT INTO Address (zipcode, street_num, street_name) VALUES (?, ?, ?)',
                    (zipcode, street_num, street_name)
                )
                address_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                
                # Link address to buyer
                conn.execute(
                    'UPDATE Buyer SET buyer_address_id = ? WHERE email = ?',
                    (address_id, user_email)
                )
        
        # Handle password change
        if current_password and new_password and confirm_password:
            if new_password != confirm_password:
                conn.close()
                flash('New passwords do not match!')
                return redirect(url_for('buyer_dashboard', tab='profile'))
            
            # Verify current password
            user = conn.execute(
                'SELECT * FROM Users WHERE email = ?', 
                (user_email,)
            ).fetchone()
            
            current_hash = hashlib.sha256(current_password.encode('utf-8')).hexdigest()
            
            if user and user['password'] == current_hash:
                # Update password
                new_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
                conn.execute(
                    'UPDATE Users SET password = ? WHERE email = ?',
                    (new_hash, user_email)
                )
                flash('Password updated successfully!')
            else:
                conn.close()
                flash('Current password is incorrect!')
                return redirect(url_for('buyer_dashboard', tab='profile'))
        
        conn.commit()
        conn.close()
        flash('Profile updated successfully!')
        return redirect(url_for('buyer_dashboard', tab='profile'))
    
    # Similar logic for other user types
    elif user_type == 'seller':
        # Handle seller profile update
        conn = get_db_connection()
        flash('Seller profile update functionality will be implemented soon.')
        conn.close()
        return redirect(url_for('seller_dashboard'))
    
    elif user_type == 'helpdesk':
        # Handle helpdesk profile update
        conn = get_db_connection()
        flash('Helpdesk profile update functionality will be implemented soon.')
        conn.close()
        return redirect(url_for('helpdesk_dashboard'))
    
    return redirect(url_for('dashboard'))

@app.route('/order/<int:order_id>')
def view_order(order_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get order details
    order = None
    
    if session['user_type'] == 'buyer':
        order = conn.execute(
            '''SELECT o.*, pl.Product_Title, pl.Product_Description, pl.Product_Price,
                  s.business_name AS seller_name, s.email AS seller_email,
                  (SELECT COUNT(*) FROM Reviews r WHERE r.Order_ID = o.Order_ID) > 0 AS has_review
               FROM Orders o
               JOIN Product_Listings pl ON o.Listing_ID = pl.Listing_ID
               JOIN Sellers s ON pl.Seller_Email = s.email
               WHERE o.Order_ID = ? AND o.Buyer_Email = ?''',
            (order_id, session['user_email'])
        ).fetchone()
    elif session['user_type'] == 'seller':
        order = conn.execute(
            '''SELECT o.*, pl.Product_Title, pl.Product_Description, pl.Product_Price,
                  b.business_name AS buyer_name, b.email AS buyer_email,
                  (SELECT COUNT(*) FROM Reviews r WHERE r.Order_ID = o.Order_ID) > 0 AS has_review
               FROM Orders o
               JOIN Product_Listings pl ON o.Listing_ID = pl.Listing_ID
               JOIN Buyer b ON o.Buyer_Email = b.email
               WHERE o.Order_ID = ? AND pl.Seller_Email = ?''',
            (order_id, session['user_email'])
        ).fetchone()
    elif session['user_type'] == 'helpdesk':
        order = conn.execute(
            '''SELECT o.*, pl.Product_Title, pl.Product_Description, pl.Product_Price,
                  s.business_name AS seller_name, s.email AS seller_email,
                  b.business_name AS buyer_name, b.email AS buyer_email,
                  (SELECT COUNT(*) FROM Reviews r WHERE r.Order_ID = o.Order_ID) > 0 AS has_review
               FROM Orders o
               JOIN Product_Listings pl ON o.Listing_ID = pl.Listing_ID
               JOIN Sellers s ON pl.Seller_Email = s.email
               JOIN Buyer b ON o.Buyer_Email = b.email
               WHERE o.Order_ID = ?''',
            (order_id,)
        ).fetchone()
    
    if not order:
        conn.close()
        flash('Order not found or access denied')
        return redirect(url_for(f'{session["user_type"]}_dashboard'))
    
    # Get review if exists
    review = conn.execute(
        'SELECT * FROM Reviews WHERE Order_ID = ?',
        (order_id,)
    ).fetchone()
    
    conn.close()
    
    return render_template(
        'order_detail.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        order=order,
        review=review
    )

@app.route('/payment/add', methods=['GET', 'POST'])
def add_payment():
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get payment details
        card_num = request.form.get('credit_card_num', '')
        card_type = request.form.get('card_type', '')
        expire_month = request.form.get('expire_month', '')
        expire_year = request.form.get('expire_year', '')
        security_code = request.form.get('security_code', '')
        
        # Validation
        if not card_num or not card_type or not expire_month or not expire_year or not security_code:
            flash('All payment fields are required')
            return render_template('add_payment.html', user_email=session['user_email'], user_type=session['user_type'])
        
        conn = get_db_connection()
        
        # Check if card already exists
        existing_card = conn.execute(
            'SELECT * FROM Credit_Cards WHERE credit_card_num = ?',
            (card_num,)
        ).fetchone()
        
        if existing_card:
            conn.close()
            flash('This card is already registered')
            return render_template('add_payment.html', user_email=session['user_email'], user_type=session['user_type'])
        
        # Add new card
        conn.execute(
            '''INSERT INTO Credit_Cards 
               (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (card_num, card_type, expire_month, expire_year, security_code, session['user_email'])
        )
        
        conn.commit()
        conn.close()
        
        flash('Payment method added successfully!')
        return redirect(url_for('buyer_dashboard', tab='profile'))

    return render_template('add_payment.html', user_email=session['user_email'], user_type=session['user_type'])

@app.route('/payment/<card_num>/edit', methods=['GET', 'POST'])
def edit_payment(card_num):
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check if card exists and belongs to the user
    card = conn.execute(
        'SELECT * FROM Credit_Cards WHERE credit_card_num = ? AND Owner_email = ?',
        (card_num, session['user_email'])
    ).fetchone()
    
    if not card:
        conn.close()
        flash('Payment method not found')
        return redirect(url_for('buyer_dashboard', tab='profile'))
    
    if request.method == 'POST':
        # Get updated payment details
        card_type = request.form.get('card_type', '')
        expire_month = request.form.get('expire_month', '')
        expire_year = request.form.get('expire_year', '')
        security_code = request.form.get('security_code', '')
        
        # Validation
        if not card_type or not expire_month or not expire_year or not security_code:
            conn.close()
            flash('All payment fields are required')
            return render_template('edit_payment.html', card=card, user_email=session['user_email'], user_type=session['user_type'])
        
        # Update card
        conn.execute(
            '''UPDATE Credit_Cards 
               SET card_type = ?, expire_month = ?, expire_year = ?, security_code = ? 
               WHERE credit_card_num = ?''',
            (card_type, expire_month, expire_year, security_code, card_num)
        )
        
        conn.commit()
        conn.close()
        
        flash('Payment method updated successfully!')
        return redirect(url_for('buyer_dashboard', tab='profile'))
    
    conn.close()
    return render_template('edit_payment.html', card=card, user_email=session['user_email'], user_type=session['user_type'])

@app.route('/payment/<card_num>/delete')
def delete_payment(card_num):
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check if card exists and belongs to the user
    card = conn.execute(
        'SELECT * FROM Credit_Cards WHERE credit_card_num = ? AND Owner_email = ?',
        (card_num, session['user_email'])
    ).fetchone()
    
    if not card:
        conn.close()
        flash('Payment method not found')
        return redirect(url_for('buyer_dashboard', tab='profile'))
    
    # Delete the card
    conn.execute(
        'DELETE FROM Credit_Cards WHERE credit_card_num = ?',
        (card_num,)
    )
    
    conn.commit()
    conn.close()
    
    flash('Payment method deleted successfully!')
    return redirect(url_for('buyer_dashboard', tab='profile'))

@app.route('/order/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    
    listing_id = request.form.get('listing_id')
    
    if not listing_id:
        flash('Invalid product selection')
        return redirect(url_for('buyer_dashboard'))
    
    # For simplicity, we'll implement direct purchase rather than a cart system
    return redirect(url_for('checkout', listing_id=listing_id))

@app.route('/checkout/<int:listing_id>', methods=['GET', 'POST'])
def checkout(listing_id):
    if 'user_email' not in session or session['user_type'] != 'buyer':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get product details
    product = conn.execute(
        '''SELECT pl.*, s.business_name AS seller_name, s.email AS seller_email
           FROM Product_Listings pl
           JOIN Sellers s ON pl.Seller_Email = s.email
           WHERE pl.Listing_ID = ? AND pl.Status = 1 ''',
        (listing_id,)
    ).fetchone()
    
    if not product:
        conn.close()
        flash('Product not available for purchase')
        return redirect(url_for('buyer_dashboard'))
    
    # Get payment methods
    payment_methods = conn.execute(
        'SELECT * FROM Credit_Cards WHERE Owner_email = ?',
        (session['user_email'],)
    ).fetchall()
    
    if request.method == 'POST':
        # Process the order
        quantity = request.form.get('quantity', '1')
        payment_method = request.form.get('payment_method')
        
        # Validation
        if not quantity.isdigit() or int(quantity) < 1 or int(quantity) > product['Quantity']:
            conn.close()
            flash('Invalid quantity')
            return render_template(
                'checkout.html',
                user_email=session['user_email'],
                user_type=session['user_type'],
                product=product,
                payment_methods=payment_methods
            )
        
        if not payment_method:
            conn.close()
            flash('Please select a payment method')
            return render_template(
                'checkout.html',
                user_email=session['user_email'],
                user_type=session['user_type'],
                product=product,
                payment_methods=payment_methods
            )
        
        # Create order
        cursor = conn.cursor()
        
        # Calculate the total payment amount
        payment_amount = float(product['Product_Price']) * int(quantity)
        
        cursor.execute(
            '''INSERT INTO Orders (Seller_Email, Listing_ID, Buyer_Email, Date, Quantity, Payment)
               VALUES (?, ?, ?, date('now'), ?, ?)''',
            (product['Seller_Email'], listing_id, session['user_email'], quantity, payment_amount)
        )
        
        order_id = cursor.lastrowid
        
        # Update product quantity
        new_quantity = product['Quantity'] - int(quantity)
        new_status = 1 if new_quantity > 0 else 2  # Use numeric status: 1 for active, 2 for sold out
        
        cursor.execute(
            'UPDATE Product_Listings SET Quantity = ?, Status = ? WHERE Listing_ID = ?',
            (new_quantity, new_status, listing_id)
        )
        
        # Update seller balance
        total_amount = product['Product_Price'] * int(quantity)
        cursor.execute(
            'UPDATE Sellers SET balance = balance + ? WHERE email = ?',
            (total_amount, product['Seller_Email'])
        )
        
        conn.commit()
        conn.close()
        
        flash('Order placed successfully!')
        
        # Always redirect back to buyer dashboard
        return redirect(url_for('buyer_dashboard', tab='orders'))
    
    conn.close()
    return render_template(
        'checkout.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        product=product,
        payment_methods=payment_methods
    )
#=======================Buyer=======================#

#=======================Seller========================#
@app.route('/seller_dashboard')
def seller_dashboard():
    # Check if user is logged in and is a seller
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    if session['user_type'] != 'seller':
        return redirect(url_for('dashboard'))
    
    # Get the current user's information
    conn = get_db_connection()
    
    # Get seller details
    seller = conn.execute(
        'SELECT * FROM Sellers WHERE email = ?', 
        (session['user_email'],)
    ).fetchone()
    
    # Get seller's address
    address = None
    if seller and seller['business_address_id']:
        address = conn.execute(
            '''SELECT a.*, z.city, z.state 
               FROM Address a 
               JOIN Zipcode_Info z ON a.zipcode = z.zipcode 
               WHERE a.address_id = ?''', 
            (seller['business_address_id'],)
        ).fetchone()
    
    # Get seller's products
    products = conn.execute(
        '''SELECT * FROM Product_Listings 
           WHERE Seller_Email = ?
           ORDER BY Listing_ID DESC''',
        (session['user_email'],)
    ).fetchall()
    
    # Count products by status
    product_count = len(products)
    active_product_count = sum(1 for p in products if p['Status'] == 1)
    
    # Get orders for seller's products
    orders = conn.execute(
        '''SELECT o.*, pl.Product_Title, pl.Product_Description, pl.Product_Price, b.email as buyer_email
           FROM Orders o
           JOIN Product_Listings pl ON o.Listing_ID = pl.Listing_ID
           JOIN Buyer b ON o.Buyer_Email = b.email
           WHERE o.Seller_Email = ?
           ORDER BY o.Date DESC''',
        (session['user_email'],)
    ).fetchall()
    
    order_count = len(orders)
    
    # Calculate total revenue
    total_revenue = sum(float(o['Product_Price']) * int(o['Quantity']) for o in orders)
    
    # Calculate average rating for this seller
    avg_rating_result = conn.execute(
        '''SELECT AVG(r.Rating) as avg_rating, COUNT(r.Rating) as review_count
           FROM Reviews r
           JOIN Orders o ON r.Order_ID = o.Order_ID
           WHERE o.Seller_Email = ?''',
        (session['user_email'],)
    ).fetchone()
    
    avg_rating = avg_rating_result['avg_rating'] if avg_rating_result and avg_rating_result['avg_rating'] is not None else None
    review_count = avg_rating_result['review_count'] if avg_rating_result else 0
    
    # Get all categories for the product form
    categories = conn.execute(
        'SELECT category_name FROM Categories ORDER BY category_name'
    ).fetchall()
    
    conn.close()
    
    # Determine active tab from query parameter or default to 'products'
    active_tab = request.args.get('tab', 'products')
    
    return render_template(
        'seller_dashboard.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        seller=seller,
        address=address,
        products=products,
        orders=orders,
        categories=categories,
        product_count=product_count,
        active_product_count=active_product_count,
        order_count=order_count,
        total_revenue=total_revenue,
        avg_rating=avg_rating,
        review_count=review_count,
        active_tab=active_tab
    )

@app.route('/seller/product/<int:listing_id>')
def get_product(listing_id):
    if 'user_email' not in session or session['user_type'] != 'seller':
        return {'error': 'Unauthorized'}, 401
    
    conn = get_db_connection()
    
    # Get product
    product = conn.execute(
        '''SELECT * FROM Product_Listings 
           WHERE Listing_ID = ? AND Seller_Email = ?''',
        (listing_id, session['user_email'])
    ).fetchone()
    
    conn.close()
    
    if not product:
        return {'error': 'Product not found'}, 404
    
    # Convert to dict for JSON response
    return {
        'Listing_ID': product['Listing_ID'],
        'Product_Title': product['Product_Title'],
        'Product_Description': product['Product_Description'],
        'Category': product['Category'],
        'Product_Price': product['Product_Price'],
        'Quantity': product['Quantity'],
        'Status': product['Status']
    }

@app.route('/seller/add_product', methods=['POST'])
def add_product():
    if 'user_email' not in session or session['user_type'] != 'seller':
        return redirect(url_for('login'))
    
    # Extract form data
    product_title = request.form.get('product_title')
    product_description = request.form.get('product_description')
    category = request.form.get('category')
    product_price = request.form.get('product_price')
    quantity = request.form.get('quantity')
    status = request.form.get('status')
    
    # For Product_Name, we can use the same value as Product_Title if no separate field exists
    product_name = product_title  
    
    # Validate inputs
    if not product_title or not product_description or not category or not product_price or not quantity or status is None:
        flash('All fields are required')
        return redirect(url_for('seller_dashboard'))
    
    # Insert product
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO Product_Listings 
           (Seller_Email, Listing_ID, Category, Product_Title, Product_Name, Product_Description, Quantity, Product_Price, Status) 
           VALUES (?, (SELECT COALESCE(MAX(Listing_ID), 0) + 1 FROM Product_Listings), ?, ?, ?, ?, ?, ?, ?)''',
        (session['user_email'], category, product_title, product_name, product_description, quantity, product_price, status)
    )
    
    conn.commit()
    conn.close()
    
    flash('Product added successfully!')
    return redirect(url_for('seller_dashboard', tab='products'))

@app.route('/seller/update_product', methods=['POST'])
def update_product():
    if 'user_email' not in session or session['user_type'] != 'seller':
        return redirect(url_for('login'))
    
    # Extract form data
    listing_id = request.form.get('listing_id')
    product_title = request.form.get('product_title')
    product_description = request.form.get('product_description')
    category = request.form.get('category')
    product_price = request.form.get('product_price')
    quantity = request.form.get('quantity')
    status = request.form.get('status')
    
    # Validate inputs
    if not listing_id or not product_title or not product_description or not category or not product_price or not quantity or status is None:
        flash('All fields are required')
        return redirect(url_for('seller_dashboard'))
    
    # Update product
    conn = get_db_connection()
    
    # Verify ownership
    product = conn.execute(
        'SELECT * FROM Product_Listings WHERE Listing_ID = ? AND Seller_Email = ?',
        (listing_id, session['user_email'])
    ).fetchone()
    
    if not product:
        conn.close()
        flash('Product not found or not authorized')
        return redirect(url_for('seller_dashboard'))
    
    # If quantity is 0, set status to "sold out" (2)
    if int(quantity) == 0:
        status = 2
    
    # Update the product
    conn.execute(
        '''UPDATE Product_Listings 
           SET Product_Title = ?, Product_Description = ?, Category = ?, 
               Product_Price = ?, Quantity = ?, Status = ?
           WHERE Listing_ID = ? AND Seller_Email = ?''',
        (product_title, product_description, category, product_price, quantity, status, listing_id, session['user_email'])
    )
    
    conn.commit()
    conn.close()
    
    flash('Product updated successfully!')
    return redirect(url_for('seller_dashboard', tab='products'))

@app.route('/seller/activate_product/<int:listing_id>')
def activate_product(listing_id):
    if 'user_email' not in session or session['user_type'] != 'seller':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Verify ownership and check quantity
    product = conn.execute(
        'SELECT * FROM Product_Listings WHERE Listing_ID = ? AND Seller_Email = ?',
        (listing_id, session['user_email'])
    ).fetchone()
    
    if not product:
        conn.close()
        flash('Product not found or not authorized')
        return redirect(url_for('seller_dashboard'))
    
    # Only activate if there's inventory
    if product['Quantity'] > 0:
        conn.execute(
            'UPDATE Product_Listings SET Status = 1 WHERE Listing_ID = ?',
            (listing_id,)
        )
        flash('Product activated successfully!')
    else:
        flash('Cannot activate product with zero quantity.')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('seller_dashboard', tab='products'))

@app.route('/seller/deactivate_product/<int:listing_id>')
def deactivate_product(listing_id):
    if 'user_email' not in session or session['user_type'] != 'seller':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Verify ownership
    product = conn.execute(
        'SELECT * FROM Product_Listings WHERE Listing_ID = ? AND Seller_Email = ?',
        (listing_id, session['user_email'])
    ).fetchone()
    
    if not product:
        conn.close()
        flash('Product not found or not authorized')
        return redirect(url_for('seller_dashboard'))
    
    # Deactivate product
    conn.execute(
        'UPDATE Product_Listings SET Status = 0 WHERE Listing_ID = ?',
        (listing_id,)
    )
    
    conn.commit()
    conn.close()
    
    flash('Product deactivated successfully!')
    return redirect(url_for('seller_dashboard', tab='products'))

@app.route('/update_seller_profile', methods=['POST'])
def update_seller_profile():
    if 'user_email' not in session or session['user_type'] != 'seller':
        return redirect(url_for('login'))
    
    # Extract form data
    business_name = request.form.get('business_name', '')
    bank_routing_number = request.form.get('bank_routing_number', '')
    bank_account_number = request.form.get('bank_account_number', '')
    
    # Address info
    street_num = request.form.get('street_num', '')
    street_name = request.form.get('street_name', '')
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    zipcode = request.form.get('zipcode', '')
    
    # Handle street and street name combined
    if not street_num and not street_name and 'street' in request.form:
        street_parts = request.form.get('street', '').split(' ', 1)
        if len(street_parts) > 0:
            street_num = street_parts[0]
        if len(street_parts) > 1:
            street_name = street_parts[1]
    
    # Password change
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    conn = get_db_connection()
    
    # Update business name and banking info
    conn.execute(
        '''UPDATE Sellers 
           SET business_name = ?, bank_routing_number = ?, bank_account_number = ? 
           WHERE email = ?''',
        (business_name, bank_routing_number, bank_account_number, session['user_email'])
    )
    
    # Handle address update
    if street_num and street_name and zipcode:
        # Check if zipcode exists
        zip_exists = conn.execute(
            'SELECT * FROM Zipcode_Info WHERE zipcode = ?', 
            (zipcode,)
        ).fetchone()
        
        if not zip_exists and city and state:
            conn.execute(
                'INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)',
                (zipcode, city, state)
            )
        
        # Get current address
        seller = conn.execute(
            'SELECT * FROM Sellers WHERE email = ?', 
            (session['user_email'],)
        ).fetchone()
        
        if seller and seller['business_address_id']:
            # Update existing address
            conn.execute(
                'UPDATE Address SET zipcode = ?, street_num = ?, street_name = ? WHERE address_id = ?',
                (zipcode, street_num, street_name, seller['business_address_id'])
            )
        else:
            # Create new address
            conn.execute(
                'INSERT INTO Address (zipcode, street_num, street_name) VALUES (?, ?, ?)',
                (zipcode, street_num, street_name)
            )
            address_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Link address to seller
            conn.execute(
                'UPDATE Sellers SET business_address_id = ? WHERE email = ?',
                (address_id, session['user_email'])
            )
    
    # Handle password change
    if current_password and new_password and confirm_password:
        if new_password != confirm_password:
            conn.close()
            flash('New passwords do not match!')
            return redirect(url_for('seller_dashboard', tab='profile'))
        
        # Verify current password
        user = conn.execute(
            'SELECT * FROM Users WHERE email = ?', 
            (session['user_email'],)
        ).fetchone()
        
        current_hash = hashlib.sha256(current_password.encode('utf-8')).hexdigest()
        
        if user and user['password'] == current_hash:
            # Update password
            new_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            conn.execute(
                'UPDATE Users SET password = ? WHERE email = ?',
                (new_hash, session['user_email'])
            )
            flash('Password updated successfully!')
        else:
            conn.close()
            flash('Current password is incorrect!')
            return redirect(url_for('seller_dashboard', tab='profile'))
    
    conn.commit()
    conn.close()
    
    flash('Profile updated successfully!')
    return redirect(url_for('seller_dashboard', tab='profile'))
#=======================Seller========================#

#=======================HelpDesk========================#
@app.route('/helpdesk_dashboard')
def helpdesk_dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    if session['user_type'] != 'helpdesk':
        return redirect(url_for('dashboard'))
    
    # Get active tab from query parameter or default to 'unassigned'
    active_tab = request.args.get('tab', 'unassigned')
    
    conn = get_db_connection()
    
    # Get helpdesk staff details
    helpdesk = conn.execute(
        'SELECT * FROM Helpdesk WHERE email = ?', 
        (session['user_email'],)
    ).fetchone()
    
    # Get unassigned requests (assigned to helpdeskteam@nittybiz.com)
    unassigned_requests = conn.execute(
        '''SELECT * FROM Requests
           WHERE helpdesk_staff_email = 'helpdeskteam@nittybiz.com'
           AND request_status = 0
           ORDER BY request_id DESC'''
    ).fetchall()
    
    # Get assigned requests (assigned to current staff)
    assigned_requests = conn.execute(
        '''SELECT * FROM Requests
           WHERE helpdesk_staff_email = ?
           AND request_status = 1
           ORDER BY request_id DESC''',
        (session['user_email'],)
    ).fetchall()
    
    # Get completed requests
    completed_requests = conn.execute(
        '''SELECT * FROM Requests
           WHERE helpdesk_staff_email = ?
           AND request_status = 2
           ORDER BY request_id DESC''',
        (session['user_email'],)
    ).fetchall()
    
    # Count requests
    unassigned_count = len(unassigned_requests)
    assigned_count = len(assigned_requests)
    completed_count = conn.execute(
        '''SELECT COUNT(*) FROM Requests
           WHERE helpdesk_staff_email = ?
           AND request_status = 2''',
        (session['user_email'],)
    ).fetchone()[0]
    
    conn.close()
    
    return render_template(
        'helpdesk_dashboard.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        position=helpdesk['position'] if helpdesk else '',
        unassigned_requests=unassigned_requests,
        assigned_requests=assigned_requests,
        completed_requests=completed_requests,
        unassigned_count=unassigned_count,
        assigned_count=assigned_count,
        completed_count=completed_count,
        active_tab=active_tab
    )

@app.route('/view_request/<int:request_id>')
def view_request(request_id):
    if 'user_email' not in session or session['user_type'] != 'helpdesk':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get request details
    request = conn.execute(
        'SELECT * FROM Requests WHERE request_id = ?',
        (request_id,)
    ).fetchone()
    
    if not request:
        conn.close()
        flash('Request not found')
        return redirect(url_for('helpdesk_dashboard'))
    
    # Get all categories for category form
    categories = conn.execute(
        'SELECT * FROM Categories ORDER BY category_name'
    ).fetchall()
    
    conn.close()
    
    return render_template(
        'view_request.html',
        user_email=session['user_email'],
        user_type=session['user_type'],
        request=request,
        categories=categories
    )

@app.route('/claim_request/<int:request_id>')
def claim_request(request_id):
    if 'user_email' not in session or session['user_type'] != 'helpdesk':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check if request exists and is unassigned
    request = conn.execute(
        '''SELECT * FROM Requests 
           WHERE request_id = ? 
           AND helpdesk_staff_email = 'helpdeskteam@nittybiz.com'
           AND request_status = 0''',
        (request_id,)
    ).fetchone()
    
    if not request:
        conn.close()
        flash('Request not found or already assigned')
        return redirect(url_for('helpdesk_dashboard'))
    
    # Assign request to current staff member
    conn.execute(
        '''UPDATE Requests 
           SET helpdesk_staff_email = ?, request_status = 1
           WHERE request_id = ?''',
        (session['user_email'], request_id)
    )
    
    conn.commit()
    conn.close()
    
    flash('Request successfully claimed')
    return redirect(url_for('helpdesk_dashboard', tab='assigned'))

@app.route('/complete_request/<int:request_id>', methods=['GET', 'POST'])
def complete_request(request_id):
    if 'user_email' not in session or session['user_type'] != 'helpdesk':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check if request exists and is assigned to current staff
    helpdesk_request = conn.execute(
        '''SELECT * FROM Requests 
           WHERE request_id = ? 
           AND helpdesk_staff_email = ?
           AND request_status = 1''',
        (request_id, session['user_email'])
    ).fetchone()
    
    if not helpdesk_request:
        conn.close()
        flash('Request not found or not assigned to you')
        return redirect(url_for('helpdesk_dashboard'))
    
    # Handle form submission for adding category
    if request.method == 'POST' and helpdesk_request['request_type'] == 'Add New Category':
        category_name = request.form.get('category_name')
        parent_category = request.form.get('parent_category') or None
        
        # Check if category already exists
        existing_category = conn.execute(
            'SELECT * FROM Categories WHERE category_name = ?',
            (category_name,)
        ).fetchone()
        
        if existing_category:
            conn.close()
            flash('Category already exists')
            return redirect(url_for('view_request', request_id=request_id))
        
        # Add new category
        conn.execute(
            'INSERT INTO Categories (category_name, parent_category) VALUES (?, ?)',
            (category_name, parent_category)
        )
        
        # Mark request as completed
        conn.execute(
            'UPDATE Requests SET request_status = 2 WHERE request_id = ?',
            (request_id,)
        )
        
        conn.commit()
        conn.close()
        
        flash('Category added and request marked as completed')
        return redirect(url_for('helpdesk_dashboard', tab='completed'))
    
    # For GET requests, show form to complete the request
    if helpdesk_request['request_type'] == 'Add New Category':
        # Get all categories for parent selection
        categories = conn.execute(
            'SELECT * FROM Categories ORDER BY category_name'
        ).fetchall()
        
        conn.close()
        
        return render_template(
            'add_category.html',
            user_email=session['user_email'],
            user_type=session['user_type'],
            request=helpdesk_request,
            categories=categories
        )

    conn.execute(
        'UPDATE Requests SET request_status = 2 WHERE request_id = ?',
        (request_id,)
    )
    
    conn.commit()
    conn.close()
    
    flash('Request marked as completed')
    return redirect(url_for('helpdesk_dashboard', tab='completed'))

@app.route('/submit_request', methods=['GET', 'POST'])
def submit_request():
    if 'user_email' not in session or session['user_type'] not in ['buyer', 'seller']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        request_type = request.form.get('request_type')
        request_desc = request.form.get('request_desc')
        
        if not request_type or not request_desc:
            flash('All fields are required')
            return render_template('submit_request.html', user_email=session['user_email'], user_type=session['user_type'])
        
        conn = get_db_connection()
        
        # Create new request
        conn.execute(
            '''INSERT INTO Requests 
               (sender_email, helpdesk_staff_email, request_type, request_desc, request_status) 
               VALUES (?, 'helpdeskteam@nittybiz.com', ?, ?, 0)''',
            (session['user_email'], request_type, request_desc)
        )
        
        conn.commit()
        conn.close()
        
        flash('Your request has been submitted')
        return redirect(url_for(f'{session["user_type"]}_dashboard'))
    
    # Show request form
    return render_template(
        'submit_request.html',
        user_email=session['user_email'],
        user_type=session['user_type']
    )

@app.route('/create_helpdesk_user', methods=['GET', 'POST'])
def create_helpdesk_user():
    # Authorization Check 
    if 'user_email' not in session or session.get('user_type') != 'helpdesk':
        flash("You are not authorized to access this page.", "error")
        return redirect(url_for('login')) # Or redirect to their own dashboard

    error = None 

    if request.method == 'POST':
        email = request.form.get('email')
        position = request.form.get('position')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Basic Validation
        if not email or not position or not password or not confirm_password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
             error = "Invalid email format."

        if error:
            # Re-render the form with the error message
            return render_template('create_helpdesk_user.html', error=error, user_email=session['user_email'], user_type=session['user_type'])

        conn = None 
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            existing_user = cursor.execute('SELECT email FROM Users WHERE email = ?', (email,)).fetchone()
            if existing_user:
                error = "Email address already exists."
                conn.close()
                return render_template('create_helpdesk_user.html', error=error, user_email=session['user_email'], user_type=session['user_type'])

            # Hash the password
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

            # Insert into Users table
            cursor.execute('INSERT INTO Users (email, password) VALUES (?, ?)', (email, password_hash))

            # Insert into Helpdesk table
            cursor.execute('INSERT INTO Helpdesk (email, position) VALUES (?, ?)', (email, position))

            conn.commit()
            flash(f"Helpdesk user '{email}' created successfully!", "success")
            return redirect(url_for('helpdesk_dashboard')) # Redirect back to dashboard

        except sqlite3.Error as e:
            if conn:
                conn.rollback() # Rollback changes on error
            error = f"Database error: {e}"
            print(f"Database error creating helpdesk user: {e}") 
            return render_template('create_helpdesk_user.html', error=error, user_email=session['user_email'], user_type=session['user_type'])
        except Exception as e:
            # Catch any other unexpected errors
             if conn:
                conn.rollback()
             error = f"An unexpected error occurred: {e}"
             print(f"Unexpected error creating helpdesk user: {e}")
             return render_template('create_helpdesk_user.html', error=error, user_email=session['user_email'], user_type=session['user_type'])
        finally:
            if conn:
                conn.close()

    return render_template('create_helpdesk_user.html', user_email=session['user_email'], user_type=session['user_type'])
#=======================HelpDesk========================#


#=======================AllThree========================#
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
#=======================AllThree========================#

if __name__ == '__main__':
    app.run(debug=True)