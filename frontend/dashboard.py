import requests
import tkinter as tk
from tkinter import ttk, messagebox
from api_client import APIClient
from book_management import BookManagement
from PIL import Image, ImageTk
from reports_fines import ReportsFines
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"  # or your actual backend URL


class AdminPage:
    def __init__(self, root, token):
        self.root = root
        self.token = token

        # ✅ Create Admin Panel Window
        self.admin_window = tk.Toplevel(self.root)
        self.admin_window.title("Admin Panel")
        self.admin_window.geometry("800x600")

        # ✅ Create Sidebar & Query Box
        self.setup_sidebar()
        #self.setup_query_box()

    def setup_sidebar(self):
        """✅ Create sidebar buttons for admin actions."""
        self.sidebar = tk.Frame(self.admin_window, bg="lightgray", width=200)
        self.sidebar.pack(side="left", fill="y")

        # ✅ Ensure all required admin buttons exist
        tk.Button(self.sidebar, text="Add User", command=self.open_add_user_window, bg="green", fg="white").pack(pady=5, padx=5, fill="x")
        tk.Button(self.sidebar, text="Remove User", command=self.open_remove_user_window, bg="red", fg="white").pack(pady=5, padx=5, fill="x")
        tk.Button(self.sidebar, text="Make Admin", command=self.open_make_admin_window, bg="blue", fg="white").pack(pady=5, padx=5, fill="x")
        tk.Button(self.sidebar, text="List Users", command=self.open_list_users_window, bg="purple", fg="white").pack(pady=5, padx=5, fill="x")
        tk.Button(self.sidebar, text="Activate User", command=self.open_activate_user_window, bg="orange", fg="white").pack(pady=5, padx=5, fill="x")
        tk.Button(self.sidebar, text="Deactivate User", command=self.open_deactivate_user_window, bg="gray", fg="white").pack(pady=5, padx=5, fill="x")

    # def setup_query_box(self):
    #     """✅ Add a text box to display SQL queries."""
    #     self.query_box = tk.Text(self.admin_window, height=10, width=80, wrap="word", bg="black", fg="white")
    #     self.query_box.pack(padx=10, pady=10, fill="both", expand=True)

    # def display_query(self, query):
    #     """✅ Append executed queries to the query display box."""
    #     self.query_box.insert(tk.END, f"{query}\n\n")
    #     self.query_box.see(tk.END)

    ### ✅ Admin Actions

    

    def open_list_users_window(self):
        """✅ Open a window to display all users."""
        list_users_window = tk.Toplevel(self.admin_window)
        list_users_window.title("List Users")
        list_users_window.geometry("600x400")  # Adjusted for better layout

        # ✅ Load and set background image
        bg_image_path = "user2.jpg"  # Ensure this image exists in your project
        try:
            bg_image = Image.open(bg_image_path).resize((600, 400), Image.Resampling.LANCZOS)
            self.list_users_bg_photo = ImageTk.PhotoImage(bg_image)
        except Exception as e:
            print(f"Error loading image: {e}")  # Debugging in case image is missing
            return  # Exit function if image fails to load

        # ✅ Create Canvas and set background
        canvas = tk.Canvas(list_users_window, width=600, height=400)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self.list_users_bg_photo, anchor="nw")

        # ✅ Create Treeview inside a frame to ensure visibility
        frame = tk.Frame(list_users_window, bg="white")
        frame.place(x=50, y=50, width=500, height=300)

        tree = ttk.Treeview(frame, columns=("ID", "Email", "Role", "Status"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Email", text="Email")
        tree.heading("Role", text="Role")

        # ✅ Set column widths for better readability
        tree.column("ID", width=50, anchor="center")
        tree.column("Email", width=50, anchor="center")
        tree.column("Role", width=70, anchor="center")
        tree.column("Status", width=50, anchor="center")  # ✅ Show Active/Inactive

        tree.pack(fill="both", expand=True)

        # ✅ Fetch users and populate the Treeview
        self.fetch_users(tree)

    def fetch_users(self, tree):
        """✅ Fetch users from the backend and display them in the Treeview."""
        try:
            response = requests.get(f"{BASE_URL}/users", headers={"Authorization": f"Bearer {self.token}"})
            response.raise_for_status()
            data = response.json()

            users = data.get("users", [])
            queries = data.get("queries", [])

            # ✅ Show query popup safely
            if hasattr(self, "show_query_window"):
                self.show_query_window(queries)  # ✅ No error now!

            # ✅ Populate Treeview with user data
            tree.delete(*tree.get_children())  # Clear previous data
            for user in users:
                status = "Active" if user["is_active"] else "Inactive"  # ✅ Convert boolean to text
                tree.insert("", "end", values=(user["id"], user["email"], user["role"], status))  # ✅ Include status

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch users: {e}")


    def open_deactivate_user_window(self):
        """✅ Open a window to deactivate a user."""
        deactivate_user_window = tk.Toplevel(self.admin_window)
        deactivate_user_window.title("Deactivate User")
        deactivate_user_window.geometry("500x350")  # Adjusted to fit background

        # ✅ Load and set background image (if needed)
        bg_image_path = "user3.jpg"  # Make sure this image exists
        try:
            bg_image = Image.open(bg_image_path).resize((500, 350), Image.Resampling.LANCZOS)
            self.deactivate_user_bg_photo = ImageTk.PhotoImage(bg_image)
            canvas = tk.Canvas(deactivate_user_window, width=500, height=350)
            canvas.pack(fill="both", expand=True)
            canvas.create_image(0, 0, image=self.deactivate_user_bg_photo, anchor="nw")
        except Exception as e:
            print(f"Error loading image: {e}")  # Debugging in case image is missing

        # ✅ Create input fields
        tk.Label(deactivate_user_window, text="User Email:", bg="white").place(x=50, y=100)
        email_entry = tk.Entry(deactivate_user_window)
        email_entry.place(x=200, y=100, width=200)

        submit_button = tk.Button(
            deactivate_user_window, text="Submit",
            command=lambda: self.deactivate_user(email_entry.get(), deactivate_user_window),
            bg="gray", fg="white"
        )
        submit_button.place(x=200, y=150, width=100)


    def deactivate_user(self, email, window):
        """✅ Send a request to deactivate a user and show query popup."""
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
            
            # ✅ Extract and show queries
            queries = response.json().get("queries", [])
            self.show_query_window(queries)

            messagebox.showinfo("Success", "User deactivated successfully!")
            window.destroy()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to deactivate user: {e}")


    def open_add_user_window(self):
        """✅ Open a window to add a user."""
        add_user_window = tk.Toplevel(self.admin_window)
        add_user_window.title("Add User")
        add_user_window.geometry("500x350")  # Match the background image size

        # ✅ Load and set background image
        bg_image_path = "user1.jpg"  # Ensure this image exists in your project
        bg_image = Image.open(bg_image_path).resize((500, 350), Image.Resampling.LANCZOS)
        self.add_user_bg_photo = ImageTk.PhotoImage(bg_image)

        # ✅ Create Canvas and set background
        canvas = tk.Canvas(add_user_window, width=500, height=350)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self.add_user_bg_photo, anchor="nw")

        # ✅ First Name
        tk.Label(add_user_window, text="First Name:", bg="white").place(x=50, y=50)
        first_name_entry = tk.Entry(add_user_window)
        first_name_entry.place(x=200, y=50, width=200)

        # ✅ Last Name (Fix: Correct position and variable name)
        tk.Label(add_user_window, text="Last Name:", bg="white").place(x=50, y=90)
        last_name_entry = tk.Entry(add_user_window)
        last_name_entry.place(x=200, y=90, width=200)

        # ✅ Email
        tk.Label(add_user_window, text="Email:", bg="white").place(x=50, y=130)
        email_entry = tk.Entry(add_user_window)
        email_entry.place(x=200, y=130, width=200)

        # ✅ Password
        tk.Label(add_user_window, text="Password:", bg="white").place(x=50, y=170)
        password_entry = tk.Entry(add_user_window, show="*")
        password_entry.place(x=200, y=170, width=200)

        # ✅ Role Selection
        tk.Label(add_user_window, text="Role:", bg="white").place(x=50, y=210)
        role_entry = ttk.Combobox(add_user_window, values=["student", "external"])
        role_entry.place(x=200, y=210, width=200)
        role_entry.set("student")

        # ✅ Submit Button (Fix: Pass both first and last name)
        submit_button = tk.Button(
            add_user_window, text="Submit", command=lambda: self.add_user(
                first_name_entry.get(),
                last_name_entry.get(),
                email_entry.get(),
                password_entry.get(),
                role_entry.get(),
                add_user_window
            ), bg="blue", fg="white"
        )
        submit_button.place(x=200, y=260, width=100)


    def add_user(self, first_name, last_name, email, password, role, window):
        """✅ Add a user and show the SQL query."""
        if not first_name or not last_name or not email or not password:
            messagebox.showerror("Error", "All fields are required.")
            return

        new_user = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "role": role
        }

        print("📤 Sending request to /register:", new_user)  # ✅ Debugging: Print payload

        try:
            response = requests.post(
                f"{BASE_URL}/register",
                json=new_user,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            print("🔄 Response:", response.status_code, response.text)  # ✅ Debugging: Print response

            response.raise_for_status()
            messagebox.showinfo("Success", "User added successfully!")
            window.destroy()

            # ✅ Extract SQL queries and display in popup
            response_json = response.json()
            queries = response_json.get("queries", [])
            self.show_sql_query(queries)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to add user: {e}")


    def show_sql_query(self, queries):
        """✅ Display SQL queries in a dark-themed popup window."""
        if not queries:
            messagebox.showinfo("SQL Query", "No queries available.")
            return

        # ✅ Create a new Toplevel window for SQL queries
        sql_window = tk.Toplevel(self.admin_window)
        sql_window.title("Executed SQL Queries")
        sql_window.geometry("600x400")
        sql_window.configure(bg="#1e1e1e")  # Dark Background

        # ✅ Create a scrollable text widget
        text_area = tk.Text(
            sql_window, wrap="word", font=("Courier New", 12), bg="#1e1e1e", fg="#ffffff",
            insertbackground="white", relief="flat", padx=10, pady=10
        )
        text_area.pack(fill="both", expand=True, padx=10, pady=10)

        # ✅ Insert queries into the text area with spacing
        for query in queries:
            text_area.insert("end", f"{query}\n\n")

        text_area.config(state="disabled")  # Make read-only

        # ✅ Add a scrollbar
        scrollbar = tk.Scrollbar(sql_window, command=text_area.yview)
        scrollbar.pack(side="right", fill="y")
        text_area.config(yscrollcommand=scrollbar.set)

   
    def open_remove_user_window(self):
        """✅ Open the window to remove a user."""
        remove_user_window = tk.Toplevel(self.admin_window)
        remove_user_window.title("Remove User")
        remove_user_window.geometry("500x350")  # Adjusted to fit the background

        # ✅ Load and set background image
        bg_image_path = "user3.jpg"  # Ensure this image exists in your project
        bg_image = Image.open(bg_image_path).resize((500, 350), Image.Resampling.LANCZOS)
        self.remove_user_bg_photo = ImageTk.PhotoImage(bg_image)

        # ✅ Create Canvas and set background
        canvas = tk.Canvas(remove_user_window, width=500, height=350)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self.remove_user_bg_photo, anchor="nw")

        # ✅ Use `.place()` consistently (NO `row` and `column`)
        tk.Label(remove_user_window, text="User Email:", bg="white").place(x=50, y=100)
        email_entry = tk.Entry(remove_user_window)
        email_entry.place(x=200, y=100, width=200)

        submit_button = tk.Button(remove_user_window, text="Submit", command=lambda: self.remove_user(
            email_entry.get(),
            remove_user_window
        ), bg="red", fg="white")
        submit_button.place(x=200, y=150, width=100)

    def remove_user(self, email, window):
        """✅ Remove a user from the system."""
        if not email:
            messagebox.showerror("Error", "Email is required.")
            return

        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove {email}?")
        if not confirm:
            return

        try:
            # ✅ Ensure request sends JSON properly
            response = requests.delete(
                f"{BASE_URL}/users",  # ✅ Keep the correct endpoint
                json={"email": email},  # ✅ Send JSON properly
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()

            queries = response.json().get("queries", ["No SQL queries available."])
            messagebox.showinfo("Success", f"User {email} removed successfully!")
            self.show_sql_query(queries)  # ✅ Show SQL queries in popup

            window.destroy()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to remove user: {e}")


    def open_make_admin_window(self):
        """✅ Open a window to make a user an admin."""
        make_admin_window = tk.Toplevel(self.admin_window)
        make_admin_window.title("Make Admin")
        make_admin_window.geometry("500x350")  # Adjusted to fit background image

        # ✅ Load and set background image
        bg_image_path = "user4.jpg"  # Ensure this image exists in your project
        bg_image = Image.open(bg_image_path).resize((500, 350), Image.Resampling.LANCZOS)
        self.make_admin_bg_photo = ImageTk.PhotoImage(bg_image)

        # ✅ Create Canvas and set background
        canvas = tk.Canvas(make_admin_window, width=500, height=350)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self.make_admin_bg_photo, anchor="nw")

        # ✅ Use `.place()` instead of `.grid()`
        tk.Label(make_admin_window, text="User Email:", bg="white").place(x=50, y=100)
        email_entry = tk.Entry(make_admin_window)
        email_entry.place(x=200, y=100, width=200)

        submit_button = tk.Button(make_admin_window, text="Submit", command=lambda: self.make_admin(
            email_entry.get(),
            make_admin_window
        ), bg="blue", fg="white")
        submit_button.place(x=200, y=150, width=100)


    def make_admin(self, email, window):
        """✅ Promote a user to admin."""
        if not email:
            messagebox.showerror("Error", "Email is required.")
            return

        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to promote {email} to admin?")
        if not confirm:
            return

        try:
            print(f"📤 Sending request to /make-admin for email: {email}")  # ✅ Debugging
            response = requests.post(
                f"{BASE_URL}/make-admin",
                json={"email": email},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            print(f"🔄 Response Status: {response.status_code}")  # ✅ Debugging
            print(f"🔄 Response Text: {response.text}")  # ✅ Debugging

            response.raise_for_status()

            queries = response.json().get("queries", ["No SQL queries available."])
            messagebox.showinfo("Success", f"User {email} is now an admin!")
            self.show_sql_query(queries)  # ✅ Show SQL queries in popup

            window.destroy()

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to promote user: {e}")

    def open_activate_user_window(self):
        """✅ Open a window to activate a user."""
        activate_user_window = tk.Toplevel(self.admin_window)
        activate_user_window.title("Activate User")
        activate_user_window.geometry("500x350")  # Adjusted to match image size

        # ✅ Load and set background image
        bg_image_path = "user5.jpg"  # Ensure this image exists in your project
        try:
            bg_image = Image.open(bg_image_path).resize((500, 350), Image.Resampling.LANCZOS)
            self.activate_user_bg_photo = ImageTk.PhotoImage(bg_image)
        except Exception as e:
            print(f"Error loading image: {e}")  # Debugging in case image is missing
            return  # Exit function if image fails to load

        # ✅ Create Canvas and set background
        canvas = tk.Canvas(activate_user_window, width=500, height=350)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self.activate_user_bg_photo, anchor="nw")

        # ✅ Place UI elements correctly
        tk.Label(activate_user_window, text="User Email:", bg="white").place(x=50, y=100)
        email_entry = tk.Entry(activate_user_window)
        email_entry.place(x=200, y=100, width=200)

        submit_button = tk.Button(
            activate_user_window, text="Activate", command=lambda: self.activate_user(
                email_entry.get(), activate_user_window
            ), bg="green", fg="white"
        )
        submit_button.place(x=200, y=160, width=100)

    def activate_user(self, email, window):
        """✅ Send a request to activate a user and show query popup."""
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

            # ✅ Extract and show queries
            queries = response.json().get("queries", [])
            self.show_query_window(queries)

            messagebox.showinfo("Success", "User activated successfully!")
            window.destroy()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to activate user: {e}")



class Dashboard:
    def __init__(self, root, token, borrower_id, is_admin=True, user_id=None):
        self.root = root
        self.token = token
        self.borrower_id = borrower_id
        self.is_admin = is_admin  # Add a flag to check if the user is an admin
        self.user_id = user_id  # ✅ Store user_id here
        self.admin_window = None  # ✅ 

        # Load the UI elements
        self.load_background_image()

        # Add widgets on top of the background
        self.setup_search_frame()  # 1️⃣ Draw search bar first (topmost) 
        self.setup_buttons()       # 2️⃣ Place buttons below the search bar
        self.setup_treeview()      # 3️⃣ Finally, add the book list below everything
        tk.Button(self.button_frame, text="View Queries", command=self.view_borrowed_books, bg="gray", fg="white", width=20).pack(pady=5)


        self.setup_query_box()  # ✅ Ensure query box is initialized

        # Create a new window for the admin page
        #self.admin_window = tk.Toplevel(self.root)
        #self.admin_window.title("Admin Panel")
        #self.admin_window.geometry("800x600")

                # Add "Admin Panel" button if the user is an admin
        if self.is_admin:
           self.setup_admin_button()

         # Add widgets for admin functionalities
        #self.setup_sidebar()
        #self.setup_query_box()  # ✅ Call this to ensure queries are displayed


    def setup_query_box(self):
        """Ensure query box is initialized and clearly visible on the UI."""
        if not hasattr(self, "query_box"):
            self.query_box = tk.Text(self.root, height=8, width=80, wrap="word", bg="black", fg="white")
            self.query_box.pack(padx=10, pady=10, side="bottom", fill="both", expand=True)  # Adjust placement to bottom




    def display_query(self, query):
        """✅ Append executed queries to the query display box."""
        print(f"🛠 Displaying Query in UI: {query}")  # ✅ Debugging: Confirm queries reach UI

        if hasattr(self, "query_box"):  # ✅ Ensure query_box exists
            self.query_box.insert(tk.END, f"{query}\n\n")
            self.query_box.see(tk.END)  # ✅ Auto-scroll
        else:
            print("⚠️ Query box not found!")  # ✅ Debugging if query_box isn't created



    def setup_admin_button(self):
         """Add a button to open the admin panel."""
         admin_button = tk.Button(self.canvas, text="Admin Panel", command=self.open_admin_page, bg="teal", fg="white")
         self.canvas.create_window(750, 50, window=admin_button)  # Adjust position

    def open_admin_page(self):
        """Open the admin page."""
        AdminPage(self.root, self.token)


    def load_background_image(self):
        """Loads and sets the background image."""
        try:
            image_path = "dashboard.jpg"  # Ensure this image exists in the same directory
            image = Image.open(image_path)
            image = image.resize((900, 900), Image.Resampling.LANCZOS)  # Resize to fit the window

            self.bg_photo = ImageTk.PhotoImage(image)

            # Create a Canvas to hold the image and widgets
            self.canvas = tk.Canvas(self.root, width=900, height=900)
            self.canvas.pack(fill="both", expand=True)

            # Set the image as a background
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        except Exception as e:
            print(f"Error loading background image: {e}")  # Debugging if image fails to load

    def setup_treeview(self):
        """Set up the Treeview for displaying books."""
        self.tree = ttk.Treeview(
            self.canvas,  
            columns=("ID", "Title", "Author", "Available", "Location"),  # , "ISBN", "Location", "Date Added", ""
            show="headings"
        )

        # Adjust column widths for better fitting
        column_widths = {
            "ID": 50,
            "Title": 200,
            "Author": 150,
            "Available": 120,
            #"ISBN": 120,
            "Location": 100,
            #"Date Added": 150,
            #"Category": 80
            
        }

        # Set column headings and widths
        for col, width in column_widths.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")  # Center align for readability

        # Adjust position to avoid text cutting off (move left)
        self.tree_window = self.canvas.create_window(450, 550, window=self.tree, width=900, height=180)



    def setup_search_frame(self):
        """Set up the search frame to align fields correctly."""
        self.search_frame = tk.Frame(self.canvas, bg="white")
        
        # Define fields for search
        fields = ["Title", "Author", "ISBN", "Category"]
        self.entries = {}  # Dictionary to store entry widgets

        for i, field in enumerate(fields):
            tk.Label(self.search_frame, text=f"{field}:", bg="white").grid(row=0, column=i * 2, padx=5, pady=5)
            entry = tk.Entry(self.search_frame, width=20)
            entry.grid(row=0, column=(i * 2) + 1, padx=5, pady=5)
            self.entries[field.lower()] = entry  # Store reference in dictionary

        # Search Button
        self.search_button = tk.Button(self.search_frame, text="Search", command=self.search_books, bg="blue", fg="white")
        self.search_button.grid(row=0, column=len(fields) * 2, padx=5, pady=5)

        # Place the search frame on the canvas
        self.search_frame_window = self.canvas.create_window(450, 80, window=self.search_frame)


    def setup_buttons(self):
        """Set up the action buttons in a vertical layout below the search bar."""
        self.button_frame = tk.Frame(self.canvas, bg="white")

        # Define buttons with their respective commands and colors
        buttons = [
            ("Add Book", self.open_add_book_window, "green"),
            ("Borrow Book", self.borrow_selected_book, "blue"),
            ("Return Book", self.return_selected_book, "red"),
            ("View Borrowed Books", self.view_borrowed_books, "purple"),
            ("Reports & Fines", self.view_reports_and_fines, "orange"),
        ]

        # Arrange buttons **vertically** using `.pack()`
        for text, command, color in buttons:
            tk.Button(self.button_frame, text=text, command=command, bg=color, fg="white", width=20).pack(pady=5)

        # Place the button frame **below the search bar**
        self.button_frame_window = self.canvas.create_window(500, 300, window=self.button_frame)


#from PIL import Image, ImageTk  # Ensure you have imported this at the top

    def open_add_book_window(self):
        """Open a new window for adding a book with a background image."""
        add_book_window = tk.Toplevel(self.root)
        add_book_window.title("Add Book")
        add_book_window.geometry("400x300")

        # Load and set the background image
        try:
            image_path = "form.jpg"  # Ensure this image exists in the same directory
            bg_image = Image.open(image_path)
            bg_image = bg_image.resize((400, 300), Image.Resampling.LANCZOS)  # Resize to fit the window
            self.form_bg_photo = ImageTk.PhotoImage(bg_image)

            # Create a Canvas to hold the image and widgets
            canvas = tk.Canvas(add_book_window, width=400, height=300)
            canvas.pack(fill="both", expand=True)

            # Set the image as a background
            canvas.create_image(0, 0, image=self.form_bg_photo, anchor="nw")

        except Exception as e:
            print(f"Error loading background image: {e}")  # Debugging if image fails to load

        # Label and Entry for Title
        tk.Label(add_book_window, text="Title:", bg="white").place(x=30, y=30)
        title_entry = tk.Entry(add_book_window)
        title_entry.place(x=150, y=30, width=200)

        # Label and Entry for Author
        tk.Label(add_book_window, text="Author:", bg="white").place(x=30, y=60)
        author_entry = tk.Entry(add_book_window)
        author_entry.place(x=150, y=60, width=200)

        # Label and Entry for Category ID
        tk.Label(add_book_window, text="Category ID:", bg="white").place(x=30, y=90)
        category_id_entry = tk.Entry(add_book_window)
        category_id_entry.place(x=150, y=90, width=200)

        # Label and Entry for ISBN
        tk.Label(add_book_window, text="ISBN:", bg="white").place(x=30, y=120)
        isbn_entry = tk.Entry(add_book_window)
        isbn_entry.place(x=150, y=120, width=200)

        # Label and Entry for Location
        tk.Label(add_book_window, text="Location:", bg="white").place(x=30, y=150)
        location_entry = tk.Entry(add_book_window)
        location_entry.place(x=150, y=150, width=200)

        # Label and Entry for Quantity
        tk.Label(add_book_window, text="Quantity:", bg="white").place(x=30, y=180)
        quantity_entry = tk.Entry(add_book_window)
        quantity_entry.place(x=150, y=180, width=200)

        # Submit Button
        submit_button = tk.Button(add_book_window, text="Submit", command=lambda: self.add_book(
            title_entry.get(),
            author_entry.get(),
            category_id_entry.get(),
            isbn_entry.get(),
            location_entry.get(),
            quantity_entry.get(),
            add_book_window
        ), bg="blue", fg="white")
        submit_button.place(x=150, y=230, width=100)


    def show_query_window(self, queries):
        """✅ Display a popup window with executed SQL queries."""
        query_window = tk.Toplevel(self.admin_window)
        query_window.title("Executed Queries")
        query_window.geometry("500x300")

        # ✅ Create a text widget to display queries
        text_widget = tk.Text(query_window, wrap="word", bg="black", fg="green", font=("Courier", 10))
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # ✅ Insert queries into the text widget
        for query in queries:
            text_widget.insert("end", f"{query}\n\n")

        text_widget.config(state="disabled")  # Make text read-only


    def add_book(self, title, author, category_id_str, isbn, location, quantity_str, window):
        """Handle adding a book and ensure all required fields are stored."""

        if not self.token:
            messagebox.showerror("Error", "You must be logged in to add a book.")
            return

        if not title or not author or not isbn or not category_id_str or not quantity_str:
            messagebox.showerror("Error", "Title, Author, ISBN, Category ID, and Quantity are required.")
            return

        try:
            category_id = int(category_id_str)  # Convert category ID to integer
            quantity = int(quantity_str)  # Convert quantity to integer
        except ValueError:
            messagebox.showerror("Error", "Category ID and Quantity must be valid numbers.")
            return

        added_by_id = self.user_id  # Store admin ID

        new_book = {
            "title": title,
            "author": author,
            "category_id": category_id,
            "isbn": isbn,
            "location": location if location else "Unknown",
            "quantity": quantity,
            "original_quantity": quantity,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "added_by_id": added_by_id,
            "is_available": 1,
        }

        try:
            response = APIClient.add_book(self.token, new_book)

            try:
                response_data = response.json()  # Convert response to JSON
            except ValueError:
                response_data = {}  # If JSON conversion fails, use an empty dict

            queries = response_data.get("queries", [])  # ✅ Extract executed queries

            if response.status_code == 201:
                messagebox.showinfo("Success", "Book added successfully!")
                window.destroy()
                self.fetch_books()  # Refresh UI immediately
                self.show_query_window(queries)  # ✅ Show the executed queries
            else:
                error_message = response_data.get("message", "Unknown error")
                messagebox.showerror("Error", f"Failed to add book: {error_message}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to add book: {str(e)}")


    def setup_query_box(self):
        """✅ Creates a text box to display executed SQL queries in the UI."""
        self.query_box = tk.Text(self.root, height=8, width=80, wrap="word", bg="black", fg="white")
        self.query_box.pack(padx=10, pady=10, fill="both", expand=True)


    def fetch_books(self, title=None, author=None, isbn=None, category=None):
        """Fetch and display books while ensuring SQL queries are shown."""

        if hasattr(self, "query_box"):  # ✅ Check if query_box exists before using it
            self.query_box.delete("1.0", tk.END)  # Clear previous queries

        self.tree.delete(*self.tree.get_children())  # ✅ Clear previous book results

        try:
            filters = {"title": title, "author": author, "isbn": isbn, "category": category}
            response = APIClient.fetch_books(self.token, filters)  # ✅ Fetch from API

            if isinstance(response, dict):
                books = response.get("books", [])
                queries = response.get("queries", [])  # ✅ Extract SQL queries

                # ✅ Show queries in query box
                if hasattr(self, "query_box"):  # ✅ Ensure query box exists
                    for query in queries:
                        self.query_box.insert(tk.END, f"{query}\n\n")  # ✅ Insert SQL queries
                    self.query_box.see(tk.END)  # ✅ Auto-scroll to latest query

                # ✅ Insert books into UI
                for book in books:
                    self.tree.insert("", "end", values=(
                        book.get("id"),
                        book.get("title"),
                        book.get("author"),
                        "Yes" if book.get("is_available") else "No",
                        book.get("location"),
                    ))

                if not books:
                    messagebox.showinfo("Info", "No books found with the given search criteria.")

            else:
                messagebox.showerror("Error", "Unexpected response format from API.")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch books: {e}")

    def search_books(self):
        """Fetch books based on search filters."""
        title = self.entries["title"].get().strip() if "title" in self.entries else ""
        author = self.entries["author"].get().strip() if "author" in self.entries else ""
        isbn = self.entries["isbn"].get().strip() if "isbn" in self.entries else ""
        category = self.entries["category"].get().strip() if "category" in self.entries else ""

        # ✅ Pass search filters to fetch_books
        self.fetch_books(title=title, author=author, isbn=isbn, category=category)


    def borrow_selected_book(self):
        """Borrow the selected book and display the executed SQL query."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a book to borrow.")
            return

        book_id = self.tree.item(selected_item, "values")[0]  # Get book ID from selection

        try:
            response = APIClient.borrow_book(self.token, book_id, self.borrower_id)

            response_data = response if isinstance(response, dict) else response.json()  # Ensure valid JSON

            queries = response_data.get("queries", [])  # ✅ Extract SQL queries

            if response_data.get("message") == "Book borrowed successfully":
                messagebox.showinfo("Success", "Book borrowed successfully!")
                self.fetch_books()  # Refresh book list
                self.show_query_window(queries)  # ✅ Show the executed queries
            else:
                error_message = response_data.get("error", "Unknown error")
                messagebox.showerror("Error", f"Failed to borrow book: {error_message}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to borrow book: {str(e)}")


    def return_selected_book(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a borrowed book to return.")
            return

        # Get the borrow_id from the selected item in the Treeview
        borrow_id = self.tree.item(selected_item, "values")[0]  # Assuming borrow_id is the first column

        try:
            # Send the return request to the backend
            response = requests.post(
                f"{BASE_URL}/return-book",
                json={"borrow_id": borrow_id},  # Send borrow_id
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            messagebox.showinfo("Success", "Book returned successfully!")
            self.view_borrowed_books()  # Refresh the borrowed books list
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to return book: {e}")


    def view_borrowed_books(self):
        """Fetch and display borrowed books in a larger separate window with more fields."""
        
        try:
            borrowed_data = APIClient.fetch_borrowed_books(self.token)

            if not borrowed_data:
                messagebox.showerror("Error", "Failed to fetch borrowed books.")
                return

            borrows = borrowed_data.get("borrows", [])  # Extract borrowed books
            queries = borrowed_data.get("queries", [])  # Extract queries

            print("✅ Queries Extracted:", queries)  # Debugging: Print extracted queries

            # ✅ Open a larger window for displaying borrowed books
            borrowed_window = tk.Toplevel(self.root)
            borrowed_window.title("Borrowed Books")
            borrowed_window.geometry("1000x500")  # Increased size for better visibility

            # ✅ Create a scrollable frame
            frame = tk.Frame(borrowed_window)
            frame.pack(fill="both", expand=True)

            tree_scroll = tk.Scrollbar(frame)
            tree_scroll.pack(side="right", fill="y")

            # ✅ Create TreeView with more fields
            borrowed_tree = ttk.Treeview(
                frame, 
                columns=("ID", "Title", "Author", "Borrowed By", "Given By", "Received By",
                        "Borrow Date", "Due Date", "Return Date", "Returned", "Location"), 
                show="headings", yscrollcommand=tree_scroll.set
            )
            tree_scroll.config(command=borrowed_tree.yview)

            # ✅ Define column headings
            borrowed_tree.heading("ID", text="ID")
            borrowed_tree.heading("Title", text="Title")
            borrowed_tree.heading("Author", text="Author")
            borrowed_tree.heading("Borrowed By", text="Borrowed By")
            borrowed_tree.heading("Given By", text="Given By")
            borrowed_tree.heading("Received By", text="Received By")
            borrowed_tree.heading("Borrow Date", text="Borrow Date")
            borrowed_tree.heading("Due Date", text="Due Date")
            borrowed_tree.heading("Return Date", text="Return Date")
            borrowed_tree.heading("Returned", text="Returned")
            borrowed_tree.heading("Location", text="Location")

            # ✅ Set column widths (wider for better visibility)
            borrowed_tree.column("ID", width=50, anchor="center")
            borrowed_tree.column("Title", width=200, anchor="center")
            borrowed_tree.column("Author", width=150, anchor="center")
            borrowed_tree.column("Borrowed By", width=150, anchor="center")
            borrowed_tree.column("Given By", width=150, anchor="center")
            borrowed_tree.column("Received By", width=150, anchor="center")
            borrowed_tree.column("Borrow Date", width=130, anchor="center")
            borrowed_tree.column("Due Date", width=130, anchor="center")
            borrowed_tree.column("Return Date", width=130, anchor="center")
            borrowed_tree.column("Returned", width=80, anchor="center")
            borrowed_tree.column("Location", width=120, anchor="center")

            borrowed_tree.pack(fill="both", expand=True)

            # ✅ Populate the TreeView with borrowed books
            for book in borrows:
                borrowed_tree.insert("", "end", values=(
                    book.get("id"),
                    book.get("borrowed_book"),
                    book.get("author"),
                    book.get("borrowed_by"),
                    book.get("given_by"),
                    book.get("received_by") if book.get("received_by") else "Not Received",
                    book.get("borrow_date"),
                    book.get("due_date"),
                    book.get("return_date") if book.get("return_date") else "Not Returned",
                    "Yes" if book.get("is_returned") else "No",
                    book.get("location"),
                ))

            # ✅ Show Executed Queries in a Separate Window
            self.show_query_window(queries)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch borrowed books: {str(e)}")


    def view_reports_and_fines(self):
        """Fetch and display reports and fines, ensuring queries also display in a separate window."""
        if not self.token or not self.borrower_id:
            messagebox.showerror("Error", "You must be logged in to view reports and fines.")
            return

        try:
            reports_data = APIClient.get_user_reports(self.borrower_id, self.token)
            if reports_data:
                self.display_reports(reports_data)
            else:
                messagebox.showerror("Error", "Failed to fetch reports.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch reports: {e}")


    def display_reports(self, data):
        """✅ Create fines report window with book details & queries."""
        if hasattr(self, 'reports_window') and self.reports_window.winfo_exists():
            self.reports_window.lift()
            return

        self.reports_window = tk.Toplevel(self.root)
        self.reports_window.title("Reports and Fines")
        self.reports_window.geometry("800x600")

        try:
            fines_image_path = "fines.jpg"
            fines_image = Image.open(fines_image_path).resize((800, 600), Image.Resampling.LANCZOS)
            self.fines_bg_photo = ImageTk.PhotoImage(fines_image)
            self.fines_canvas = tk.Canvas(self.reports_window, width=800, height=600)
            self.fines_canvas.pack(fill="both", expand=True)
            self.fines_canvas.create_image(0, 0, image=self.fines_bg_photo, anchor="nw")
        except Exception as e:
            print(f"Error loading background image: {e}")

        total_label = tk.Label(
            self.fines_canvas,
            text=f"Total Paid: ${data['total']['paid']} | Total Unpaid: ${data['total']['unpaid']}",
            bg="white",
            font=("Arial", 12, "bold")
        )
        self.fines_canvas.create_window(400, 50, window=total_label)

        # ✅ Setup TreeView for fines
        columns = ("ID","Amount", "Paid", "Created Date", "Paid Date")
        self.fines_tree = ttk.Treeview(self.fines_canvas, columns=columns, show="headings")

        for col in columns:
            self.fines_tree.heading(col, text=col)
            self.fines_tree.column(col, width=120, anchor="center")

        # ✅ Insert fines into UI with proper book title handling
        for fine in data["fines"]:
            self.fines_tree.insert(
                "",
                "end",
                values=(
                    fine["id"],
                    #fine.get("book_title", ""),  # ✅ Allow missing book title
                    f"${fine['amount']}",
                    "Yes" if fine["paid"] else "No",
                    fine["date_created"],
                    fine["date_paid"] if fine["date_paid"] else "Not Paid"
                )
            )

        self.fines_canvas.create_window(400, 300, window=self.fines_tree, width=700, height=250)

        # ✅ Show Executed Queries
        self.show_query_window(data.get("queries", []))

    
    def display_fines_page(self):
        """Display a page of fines."""
        start = self.current_page * self.fines_per_page
        end = start + self.fines_per_page
        fines_to_display = self.fines[start:end]

        y_offset = 150  # Initial vertical position for fines
        for fine in fines_to_display:
            fine_text = f"Fine ID: {fine['id']}, Amount: {fine['amount']}, Paid: {fine['paid']}"
            fine_label = tk.Label(self.fines_canvas, text=fine_text, bg="white")
            self.fines_canvas.create_window(180, y_offset, window=fine_label)
            y_offset += 30  # Increment vertical position for the next fine

    def prev_fines_page(self):
        """Go to the previous page of fines."""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_fines_page()

    def next_fines_page(self):
        """Go to the next page of fines."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_fines_page()