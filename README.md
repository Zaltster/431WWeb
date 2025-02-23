# Hospital Patient Management System

## 📌 Project Overview

This is a **Flask-based web application** that allows users to:

- **Add patient records** (First Name, Last Name, and Auto-Generated PID)
- **View all patients** stored in an SQLite database
- **Delete patient records** using a confirmation modal (**Bonus Feature 🎉**)
- **Use Bootstrap for styling** to improve user experience

## 🛠 Technologies Used

- **Python 3** (Flask Framework)
- **SQLite** (Database)
- **Bootstrap** (Frontend Styling)
- **VS Code** (Editor, instead of PyCharm)

---

## 🚀 Getting Started

### **1️⃣ Install Dependencies**

Before running the application, install Flask:

```sh
pip install flask
```

### **2️⃣ Clone or Download the Repository**

If using Git, clone this repository:

```sh
git clone https://github.com/Zaltster/431WWeb.git
```

Otherwise, manually download and extract the project files.

### **3️⃣ Navigate to the Project Directory**

```sh
cd Starter_Code_431W
```

### **4️⃣ Run the Flask Application**

```sh
python app.py
```

By default, the app runs on:

```
http://127.0.0.1:5000/
```

---

## 🛠 File Structure

Your project should have the following structure:

```
/project-folder
│── .idea/               # PyCharm settings (can be ignored since we use VS Code)
│── templates/           # HTML templates
│   │── index.html       # Home Page
│   │── input.html       # Add Patient Page
│   │── delete.html      # Delete Patient Page
│── app.py               # Flask Application Logic
│── database.db          # SQLite Database (auto-created)
│── README.md            # Documentation
```

---

## 🖥 Features

### ✅ **1. Add a Patient**

- Navigate to `/name`
- Enter the **First Name** and **Last Name**
- Click the **"Add" button** to store the patient in the database
- A **unique PID** is generated automatically
- The updated patient list is displayed

### ✅ **2. View Patient Records**

- All patient records are displayed on the **same page** after submission.
- Each patient has:
  - **PID** (Auto-generated)
  - **First Name**
  - **Last Name**

### ✅ **3. Delete a Patient**

- Navigate to `/delete`
- Enter the patient's **First Name** and **Last Name**
- Click **"Delete"** (A Bootstrap confirmation modal appears)
- Confirm the deletion
- The patient's record is removed from the database
- If the patient doesn’t exist, a message is displayed

### 🎉 **Bonus Feature: Bootstrap Confirmation Modal**

- Prevents accidental deletions
- Enhances user experience

---

## 📌 Troubleshooting

❌ **Flask Not Found?**  
Run:

```sh
pip install flask
```

❌ **Database Not Updating?**  
Delete `database.db` and restart the app.

❌ **Port 5000 Already in Use?**  
Run:

```sh
python app.py --port=5001
```
