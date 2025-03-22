# LibraryManagement
# 📚 Library Management System

## **🚀 Project Overview**
This is a **Library Management System** built with **Python (Flask)** for the backend and **Tkinter** for the frontend.

### **🔹 Features:**
- **User authentication** (Admin & Student roles)
- **Book borrowing & returning system**
- **Fine tracking** for late returns
- **Admin functionalities** (Manage users, books, and reports)

---
## **📥 Installation & Setup**
### **1️⃣ Clone the Repository**
Open a terminal and run:
```bash
git clone https://github.com/Lunar9999/LibraryManagement.git
cd LibraryManagement
```
---
## **⚙️ Backend Setup (API Server)**
### **2️⃣ Create & Activate a Virtual Environment**
```bash
cd backend
python -m venv venv

# Activate Virtual Environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```
### **4️⃣ Run the Backend**
```bash
python api.py
```
✅ The API will run at `http://127.0.0.1:5000`

---
## **🖥️ Frontend Setup (Tkinter GUI)**
### **5️⃣ Open a New Terminal & Navigate to Frontend**
```bash
cd ../frontend
```
### **6️⃣ Activate Virtual Environment**
```bash
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
### **7️⃣ Run the GUI**
```bash
python main.py
```
✅ The **Tkinter GUI** will launch, allowing you to manage books, borrow, and return them.

---
## **🛠️ API Endpoints**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | `POST` | Register a new user |
| `/login` | `POST` | Authenticate user and get JWT token |
| `/books` | `GET` | Fetch all books |
| `/borrow-book` | `POST` | Borrow a book |
| `/return-book` | `POST` | Return a book |
| `/fines` | `GET` | Get unpaid fines |

---
## **📌 Notes**
- Ensure **Python 3.8+** is installed.
- Always **activate the virtual environment** before running backend or frontend.
- If issues arise, check logs or errors in the terminal.

Happy coding! 🚀

