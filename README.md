# NittanyBusiness E-commerce Platform

## Overview
NittanyBusiness is a comprehensive e-commerce web application built with Python Flask and SQLite. The platform connects buyers and sellers, allowing product listings, purchases, and reviews, all managed by a helpdesk support system. Built by 2D2S

## Features

### User System
- Multiple user types: Buyers, Sellers, and Helpdesk staff
- Secure authentication with password hashing
- Profile management for all user types

### Buyer Features
- Browse product listings by category
- Search functionality with filters
- Purchase products
- View order history
- Leave product reviews
- Manage payment methods

### Seller Features
- Create and manage product listings
- Process orders
- Track sales performance and revenue
- View buyer details for completed orders

### Helpdesk Features
- Process support requests from buyers and sellers
- Manage system categories
- Create additional helpdesk accounts

## Technical Details

### Technology Stack
- **Backend**: Python Flask
- **Database**: SQLite3
- **Frontend**: HTML (jinjia), CSS, JavaScript

### Database Schema
The application uses several interconnected tables:
- Users: Core user information
- Buyers/Sellers/Helpdesk: User type-specific details
- Product_Listings: Products available for purchase
- Orders: Transaction records
- Reviews: Customer feedback
- Address: Location information
- Zipcode_Info: City/state data for zipcodes
- Credit_Cards: Payment methods for buyers
- Requests: Support tickets

## Installation

1. Clone the repository/download zip
   ```
   pip install Flask
   ```
2. Run the development server (run app.py): 
   ```
   flask run
   ```

## Usage

### For Buyers
1. Create a buyer account
2. Browse or search for products
3. Purchase items
4. Leave reviews on completed orders
5. Manage your profile and payment methods

### For Sellers
1. Create a seller account
2. Add product listings with descriptions and pricing
3. Manage inventory
4. Process incoming orders
5. View sales statistics

### For Helpdesk
1. Log in with helpdesk credentials
2. Process support requests
3. Manage product categories
4. Create additional helpdesk accounts as needed

## Project Structure
```
NittanyBusiness/
├── app.py               # Main application file
├── database.db          # SQLite database
├── static/              # Static assets (CSS, JS, images)
├── templates/           # HTML templates
│   ├── add_category.html
│   ├── add_payment.html
│   ├── buyer_dashboard.html
│   ├── checkout.html
│   ├── helpdesk_dashboard.html
│   ├── index.html
│   ├── login.html
│   ├── order_detail.html
│   ├── product_detail.html
│   ├── search_results.html
│   ├── seller_dashboard.html
│   ├── signup.html
│   └── view_request.html
└── requirements.txt     # Python dependencies
```



### Database Connection Handling
Always ensure that database connections are properly closed after operations by using the `conn.close()` method or by implementing connections within a context manager.


