import requests
import tkinter as tk
from tkinter import ttk, messagebox
from api_client import APIClient
from book_management import BookManagement
from PIL import Image, ImageTk
from reports_fines import ReportsFines

BASE_URL = "http://127.0.0.1:5000"  # or your actual backend URL


class AdminPage:
    def __init__(self, root, token):
        self.root = root
        self.token = token

        # Create a new window for the admin page
        self.admin_window = tk.Toplevel(self.root)
        self.admin_window.title("Admin Panel")
        self.admin_window.geometry("800x600")

        # Add widgets for admin functionalities
        self.setup_sidebar()

    def setup_sidebar(self):
        """Set up the sidebar for admin functionalities."""
        sidebar = tk.Frame(self.admin_window, bg="lightgray", width=200)
        sidebar.pack(side="left", fill="y")

        # Add buttons for admin actions
        tk.Button(sidebar, text="Add User", command=self.open_add_user_window, bg="green", fg="white").pack(pady=10, padx=10, fill="x")
        tk.Button(sidebar, text="Remove User", command=self.open_remove_user_window, bg="red", fg="white").pack(pady=10, padx=10, fill="x")
        tk.Button(sidebar, text="Update Books", command=self.open_update_books_window, bg="blue", fg="white").pack(pady=10, padx=10, fill="x")
        tk.Button(sidebar, text="Activate Users", command=self.open_activate_users_window, bg="orange", fg="white").pack(pady=10, padx=10, fill="x")
        tk.Button(sidebar, text="List Users", command=self.open_list_users_window, bg="purple", fg="white").pack(pady=10, padx=10, fill="x")
        tk.Button(sidebar, text="Make Admin", command=self.open_make_admin_window, bg="teal", fg="white").pack(pady=10, padx=10, fill="x")

    def open_add_user_window(self):
        """Open a new window for adding a user."""
        add_user_window = tk.Toplevel(self.admin_window)
        add_user_window.title("Add User")
        add_user_window.geometry("400x300")

        # Label and Entry for Username
        tk.Label(add_user_window, text="Username:").grid(row=0, column=0, padx=10, pady=5)
        username_entry = tk.Entry(add_user_window)
        username_entry.grid(row=0, column=1, padx=10, pady=5)

        # Label and Entry for Password
        tk.Label(add_user_window, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        password_entry = tk.Entry(add_user_window, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=5)

        # Label and Entry for Email
        tk.Label(add_user_window, text="Email:").grid(row=2, column=0, padx=10, pady=5)
        email_entry = tk.Entry(add_user_window)
        email_entry.grid(row=2, column=1, padx=10, pady=5)

        # Label and Entry for Role
        tk.Label(add_user_window, text="Role:").grid(row=3, column=0, padx=10, pady=5)
        role_entry = ttk.Combobox(add_user_window, values=["user", "admin"])
        role_entry.grid(row=3, column=1, padx=10, pady=5)
        role_entry.set("user")  # Default role

        # Submit Button
        submit_button = tk.Button(add_user_window, text="Submit", command=lambda: self.add_user(
            username_entry.get(),
            password_entry.get(),
            email_entry.get(),
            role_entry.get(),
            add_user_window
        ), bg="blue", fg="white")
        submit_button.grid(row=4, columnspan=2, pady=10)

    def add_user(self, username, password, email, role, window):
        """Handle adding a user."""
        if not username or not password or not email:
            messagebox.showerror("Error", "Username, Password, and Email are required.")
            return

        new_user = {
            "username": username,
            "password": password,
            "email": email,
            "role": role
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/users",
                json=new_user,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            messagebox.showinfo("Success", "User added successfully!")
            window.destroy()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to add user: {e}")

    def open_remove_user_window(self):
        """Open a new window for removing a user."""
        remove_user_window = tk.Toplevel(self.admin_window)
        remove_user_window.title("Remove User")
        remove_user_window.geometry("400x200")

        # Label and Entry for User ID
        tk.Label(remove_user_window, text="User ID:").grid(row=0, column=0, padx=10, pady=5)
        user_id_entry = tk.Entry(remove_user_window)
        user_id_entry.grid(row=0, column=1, padx=10, pady=5)

        # Submit Button
        submit_button = tk.Button(remove_user_window, text="Submit", command=lambda: self.remove_user(
            user_id_entry.get(),
            remove_user_window
        ), bg="red", fg="white")
        submit_button.grid(row=1, columnspan=2, pady=10)

    def remove_user(self, user_id, window):
        """Handle removing a user."""
        if not user_id:
            messagebox.showerror("Error", "User ID is required.")
            return

        try:
            response = requests.delete(
                f"{BASE_URL}/api/users/{user_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            messagebox.showinfo("Success", "User removed successfully!")
            window.destroy()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to remove user: {e}")


class Dashboard:
    def __init__(self, root, token, borrower_id, is_admin=False):
        self.root = root
        self.token = token
        self.borrower_id = borrower_id
        self.is_admin = is_admin  # Add a flag to check if the user is an admin

        # Load the background image
        self.load_background_image()

        # Add widgets on top of the background
        self.setup_treeview()
        self.setup_search_frame()
        self.setup_buttons()

        # Add "Admin Panel" button if the user is an admin
        if self.is_admin:
            self.setup_admin_button()

    def setup_admin_button(self):
        """Add a button to open the admin panel."""
        admin_button = tk.Button(self.canvas, text="Admin Panel", command=self.open_admin_page, bg="teal", fg="white")
        self.canvas.create_window(50, 50, window=admin_button)  # Position the button

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
        """Set up the Treeview on top of the background."""
        self.tree = ttk.Treeview(
            self.canvas,  # Use the canvas as the parent  or contentfarmae whichever 
            columns=("ID", "Title", "Author", "Category", "ISBN", "Location", "Date Added", "Available"), show="headings")
        
        for col in ["ID", "Title", "Author", "Category", "ISBN", "Available"]:
            self.tree.heading(col, text=col)

        # Place the Treeview on the canvas (positioned to the right)
        self.tree_window = self.canvas.create_window(400, 250, window=self.tree, width=950, height=150)

    def setup_search_frame(self):
        """Set up the search frame on top of the background."""
        self.search_frame = tk.Frame(self.canvas, bg="white")  # Use the canvas as the parent

        # Adjust the layout to ensure all fields are visible
        tk.Label(self.search_frame, text="Title:", bg="white").grid(row=0, column=0, padx=5, pady=5)
        self.title_search_entry = tk.Entry(self.search_frame, width=20)
        self.title_search_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.search_frame, text="Author:", bg="white").grid(row=0, column=2, padx=5, pady=5)
        self.author_search_entry = tk.Entry(self.search_frame, width=20)
        self.author_search_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(self.search_frame, text="ISBN:", bg="white").grid(row=1, column=0, padx=5, pady=5)
        self.isbn_search_entry = tk.Entry(self.search_frame, width=20)
        self.isbn_search_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.search_frame, text="Category:", bg="white").grid(row=1, column=2, padx=5, pady=5)
        self.category_search_entry = tk.Entry(self.search_frame, width=20)
        self.category_search_entry.grid(row=1, column=3, padx=5, pady=5)

        self.search_button = tk.Button(self.search_frame, text="Search", command=self.search_books, bg="blue", fg="white")
        self.search_button.grid(row=2, columnspan=4, pady=10)

        # Place the search frame on the canvas (positioned to the right)
        self.search_frame_window = self.canvas.create_window(600, 50, window=self.search_frame)

    def setup_buttons(self):
        """Set up the buttons frame on top of the background."""
        self.button_frame = tk.Frame(self.canvas, bg="white")
        # Position buttons in a 2x2 grid with one button below
        self.add_button = tk.Button(self.button_frame, text="Add Book", command=self.open_add_book_window, bg="green", fg="white")
        self.add_button.grid(row=0, column=0, padx=10, pady=10)
        self.borrow_button = tk.Button(self.button_frame, text="Borrow Selected Book", command=self.borrow_selected_book, bg="blue", fg="white")
        self.borrow_button.grid(row=0, column=1, padx=10, pady=10)

        self.return_button = tk.Button(self.button_frame, text="Return Selected Book", command=self.return_selected_book, bg="red", fg="white")
        self.return_button.grid(row=1, column=0, padx=10, pady=10)

        self.view_borrowed_button = tk.Button(self.button_frame, text="View Borrowed Books", command=self.view_borrowed_books, bg="purple", fg="white")
        self.view_borrowed_button.grid(row=1, column=1, padx=10, pady=10)

        # Place the "View Reports and Fines" button below the 2x2 grid
        self.reports_button = tk.Button(self.button_frame, text="View Reports and Fines", command=self.view_reports_and_fines, bg="orange", fg="white")
        self.reports_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Place the button frame on the canvas
        self.button_frame_window = self.canvas.create_window(700, 550, window=self.button_frame)

    def open_add_book_window(self):
        """Open a new window for adding a book."""
        add_book_window = tk.Toplevel(self.root)
        add_book_window.title("Add Book")
        add_book_window.geometry("400x300")

        # Label and Entry for Title
        tk.Label(add_book_window, text="Title:").grid(row=0, column=0, padx=10, pady=5)
        title_entry = tk.Entry(add_book_window)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        # Label and Entry for Author
        tk.Label(add_book_window, text="Author:").grid(row=1, column=0, padx=10, pady=5)
        author_entry = tk.Entry(add_book_window)
        author_entry.grid(row=1, column=1, padx=10, pady=5)

        # Label and Entry for Category ID
        tk.Label(add_book_window, text="Category ID:").grid(row=2, column=0, padx=10, pady=5)
        category_id_entry = tk.Entry(add_book_window)
        category_id_entry.grid(row=2, column=1, padx=10, pady=5)

        # Label and Entry for ISBN
        tk.Label(add_book_window, text="ISBN:").grid(row=3, column=0, padx=10, pady=5)
        isbn_entry = tk.Entry(add_book_window)
        isbn_entry.grid(row=3, column=1, padx=10, pady=5)

        # Label and Entry for Location
        tk.Label(add_book_window, text="Location:").grid(row=4, column=0, padx=10, pady=5)
        location_entry = tk.Entry(add_book_window)
        location_entry.grid(row=4, column=1, padx=10, pady=5)

        # Label and Entry for Quantity
        tk.Label(add_book_window, text="Quantity:").grid(row=5, column=0, padx=10, pady=5)
        quantity_entry = tk.Entry(add_book_window)
        quantity_entry.grid(row=5, column=1, padx=10, pady=5)

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
        submit_button.grid(row=6, columnspan=2, pady=10)

    def add_book(self, title, author, category_id_str, isbn, location, quantity_str, window):
        """Handle adding a book."""
        if not self.token:
            messagebox.showerror("Error", "You must be logged in to add a book.")
            return

        # Ensure required fields are not empty
        if not title or not author or not isbn or not category_id_str or not quantity_str:
            messagebox.showerror("Error", "Title, Author, ISBN, Category ID, and Quantity are required.")
            return

        # Convert category_id to integer
        try:
            category_id = int(category_id_str)  # Convert category_id to integer
        except ValueError:
            messagebox.showerror("Error", "Category ID must be a valid number.")
            return

        # Convert quantity to integer
        try:
            quantity = int(quantity_str)  # Convert quantity to integer
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a valid number.")
            return

        # Prepare the new book data
        new_book = {
            "title": title,
            "author": author,
            "category_id": category_id,  # Use the integer category_id
            "isbn": isbn,
            "location": location if location else "Unknown",  # Default to "Unknown"
            "quantity": quantity,  # Include the quantity field
            "date_added": "Sun, 02 Mar 2025 12:00:00 GMT",  # Replace with real timestamp if needed
            "is_available": True
        }

        try:
            # Ensure APIClient.add_book() sends the token in headers
            APIClient.add_book(self.token, new_book)
            messagebox.showinfo("Success", "Book added successfully!")
            window.destroy()  # Close the add book window
            self.fetch_books()  # Refresh book list
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to add book: {e}")

    def fetch_books(self, title=None, author=None, isbn=None, category=None):
        """Fetch and display books from the backend."""
        self.tree.delete(*self.tree.get_children())  # Clear the Treeview
        try:
            filters = {"title": title, "author": author, "isbn": isbn, "category": category}
            books = APIClient.fetch_books(self.token, filters)

            if isinstance(books, dict):
                books = books.get("books", [])

            for book in books:
                if isinstance(book, dict):
                    self.tree.insert("", "end", values=(
                        book.get("id"),
                        book.get("title"),
                        book.get("author"),
                        book.get("book_category"),
                        book.get("isbn"),
                        book.get("location"),
                        book.get("date_added"),
                        "Yes" if book.get("is_available") else "No"
                    ))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch books: {e}")

    def search_books(self):
        title = self.title_search_entry.get()
        author = self.author_search_entry.get()
        isbn = self.isbn_search_entry.get()
        category = self.category_search_entry.get()

        self.fetch_books(title=title, author=author, isbn=isbn, category=category)

    def borrow_selected_book(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a book to borrow.")
            return

        book_id = self.tree.item(selected_item, "values")[0]
        BookManagement.borrow_book(self.token, book_id, self.borrower_id)

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
        borrowed_books = APIClient.fetch_borrowed_books(self.token)
        print("Borrowed Books Response:", borrowed_books)  # Debugging: Print the response

        if borrowed_books:
            # Clear the Treeview
            self.tree.delete(*self.tree.get_children())

            # Insert borrowed books into the Treeview
            for book in borrowed_books:
                self.tree.insert("", "end", values=(
                    book.get("id"),  # Use "id" for borrow_id
                    book.get("borrowed_book"),  # Use "borrowed_book" for title
                    book.get("borrowed_by"),  # Use "borrowed_by" for author
                    book.get("borrow_date"),  # Use "borrow_date" for borrow date
                    book.get("due_date"),  # Use "due_date" for due date
                    "Yes" if book.get("is_returned") else "No"  # Use "is_returned" for returned status
                ))
        else:
            messagebox.showinfo("Info", "No borrowed books found.")

    def view_reports_and_fines(self):
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
        # Ensure only one window is created
        if hasattr(self, 'reports_window') and self.reports_window.winfo_exists():
            self.reports_window.lift()  # Bring the existing window to the front
            return

        # Create the reports window
        self.reports_window = tk.Toplevel(self.root)
        self.reports_window.title("Reports and Fines")
        self.reports_window.geometry("800x600")  # Set a fixed size for the window

        # Load and set the background image
        try:
            fines_image_path = "fines.jpg"  # Ensure this image exists in the same directory
            fines_image = Image.open(fines_image_path)
            fines_image = fines_image.resize((800, 600), Image.Resampling.LANCZOS)  # Resize to fit the window

            self.fines_bg_photo = ImageTk.PhotoImage(fines_image)

            # Create a Canvas to hold the image and widgets
            self.fines_canvas = tk.Canvas(self.reports_window, width=800, height=600)
            self.fines_canvas.pack(fill="both", expand=True)

            # Set the image as a background
            self.fines_canvas.create_image(0, 0, image=self.fines_bg_photo, anchor="nw")

        except Exception as e:
            print(f"Error loading background image: {e}")  # Debugging if image fails to load

        # Add user information
        user_label = tk.Label(self.fines_canvas, text=f"User ID: {self.borrower_id}", bg="white")
        self.fines_canvas.create_window(400, 50, window=user_label)

        # Display fines information with pagination
        if "fines" in data:
            fines_label = tk.Label(self.fines_canvas, text="Fines:", bg="white")
            self.fines_canvas.create_window(400, 100, window=fines_label)

            self.current_page = 0
            self.fines_per_page = 10
            self.fines = data["fines"]
            self.total_pages = (len(self.fines) // self.fines_per_page + (1 if len(self.fines) % self.fines_per_page != 0 else 0))

            self.display_fines_page()

            # Pagination controls
            self.prev_button = tk.Button(self.fines_canvas, text="Previous", command=self.prev_fines_page, bg="blue", fg="white")
            self.next_button = tk.Button(self.fines_canvas, text="Next", command=self.next_fines_page, bg="blue", fg="white")
            self.fines_canvas.create_window(300, 550, window=self.prev_button)
            self.fines_canvas.create_window(500, 550, window=self.next_button)

        # Display total paid and unpaid
        if "total" in data:
            total_label = tk.Label(self.fines_canvas, text=f"Total Paid: {data['total']['paid']}, Total Unpaid: {data['total']['unpaid']}", bg="white")
            self.fines_canvas.create_window(400, 520, window=total_label)

    def display_fines_page(self):
        """Display a page of fines."""
        start = self.current_page * self.fines_per_page
        end = start + self.fines_per_page
        fines_to_display = self.fines[start:end]

        y_offset = 150  # Initial vertical position for fines
        for fine in fines_to_display:
            fine_text = f"Fine ID: {fine['id']}, Amount: {fine['amount']}, Paid: {fine['paid']}"
            fine_label = tk.Label(self.fines_canvas, text=fine_text, bg="white")
            self.fines_canvas.create_window(400, y_offset, window=fine_label)
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