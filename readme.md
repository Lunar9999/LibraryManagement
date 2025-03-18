📌 Documentation: Enhancing User Management in Admin Panel
This documentation explains how double-clicking on a user displays the SQL query executed, as well as how to activate and deactivate users.

🔹 Feature: Display SQL Query on User Click
🛠️ Overview
When an admin lists users, they can double-click on any user entry to see the SQL queries executed when retrieving that user.

This feature helps in debugging and provides visibility into the database operations.

💡 How It Works
The list of users is fetched from the API.
Each user is displayed in a table (Treeview).
When a user is double-clicked, a popup appears showing the executed SQL query.
🔹 Implementation:
1️⃣ Fetch Users & Store Queries
The fetch_users() method retrieves users from the API.
The executed SQL queries are stored for later use.
The Treeview binds a function to handle double-clicks.
python
Copy
Edit
def fetch_users(self, tree):
    """✅ Fetch users from the backend and display them in the Treeview."""
    try:
        response = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()

        users_data = response.json()
        users = users_data.get("users", [])
        queries = users_data.get("queries", ["No SQL queries available."])

        self.user_queries = queries  # ✅ Store queries globally for later use

        # ✅ Populate Treeview with users
        for user in users:
            tree.insert("", "end", values=(user["id"], user["email"], user["role"]))

        # ✅ Bind event for double-clicking a user (Displays SQL Query)
        tree.bind("<Double-1>", lambda event: self.show_sql_query(self.user_queries))

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch users: {e}")
2️⃣ Display SQL Query in Popup
When a user is double-clicked, this function creates a popup window.
The executed SQL queries are displayed in a dark-themed text box.
python
Copy
Edit
def show_sql_query(self, queries):
    """✅ Display the executed SQL queries in a popup window."""
    query_window = tk.Toplevel(self.admin_window)
    query_window.title("Executed SQL Queries")
    query_window.geometry("600x400")

    text_widget = tk.Text(query_window, wrap="word", bg="black", fg="white", font=("Courier", 10))
    text_widget.pack(fill="both", expand=True, padx=10, pady=10)

    query_text = "\n".join(queries)
    text_widget.insert("1.0", query_text)
    text_widget.config(state="disabled")  # Prevent editing
🔹 Feature: Activate & Deactivate Users
🛠️ Overview
Admins can activate or deactivate a user via API requests.

Deactivate: The user loses access to the system.
Activate: The user is re-enabled.
🔹 Implementation
1️⃣ Deactivate User
Admin enters a user email.
Sends a POST request to /deactivate-user.
If successful, shows success message.
python
Copy
Edit
def deactivate_user(self, email, window):
    """✅ Send request to deactivate a user."""
    if not email:
        messagebox.showerror("Error", "Email is required.")
        return

    try:
        response = requests.post(
            f"{BASE_URL}/deactivate-user",
            json={"email": email},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        messagebox.showinfo("Success", "User deactivated successfully!")
        window.destroy()
        self.show_sql_query([f"UPDATE users SET is_active=0 WHERE email='{email}';"])
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to deactivate user: {e}")
2️⃣ Activate User
Admin enters a user email.
Sends a POST request to /activate-user.
If successful, shows success message.
python
Copy
Edit
def activate_user(self, email, window):
    """✅ Send request to activate a user."""
    if not email:
        messagebox.showerror("Error", "Email is required.")
        return

    try:
        response = requests.post(
            f"{BASE_URL}/activate-user",
            json={"email": email},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        messagebox.showinfo("Success", "User activated successfully!")
        window.destroy()
        self.show_sql_query([f"UPDATE users SET is_active=1 WHERE email='{email}';"])
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to activate user: {e}")
🔹 How to Use in the Admin Panel
➡️ Viewing Users
Open the Admin Panel.
Click List Users.
Users will be displayed.
➡️ Viewing SQL Queries
Double-click on a user.
A popup will appear with the executed SQL query.
➡️ Deactivating a User
Click Deactivate User.
Enter the email.
Click Submit.
The user is deactivated.
A popup will show the SQL query executed.
➡️ Activating a User
Click Activate User.
Enter the email.
Click Submit.
The user is activated.
A popup will show the SQL query executed.