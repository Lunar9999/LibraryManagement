import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from api_client import APIClient
from dashboard import Dashboard

class LoginRegister:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("1000x800")
        self.root.resizable(False, False)  # Disable resizing

        # Load Background Image
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "loginpage.jpg")

        self.bg_image = Image.open(image_path)
        self.bg_image = self.bg_image.resize((1000, 800))  # Resize to fit window
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        # Background Canvas
        self.canvas = tk.Canvas(root, width=1000, height=800)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # Create Login Form
        self.create_login_form()

    def create_login_form(self):
        # Frame for Login
        self.login_frame = tk.Frame(self.root, bg="white", bd=5)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center", width=420, height=350)

        # Title
        tk.Label(self.login_frame, text="Login", font=("Arial", 22, "bold"), bg="white", fg="black").pack(pady=10)

        # Username
        tk.Label(self.login_frame, text="Username:", bg="white", font=("Arial", 14)).pack(pady=5)
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 14))
        self.username_entry.pack(pady=5, ipady=6, ipadx=12, fill="x", padx=20)

        # Password
        tk.Label(self.login_frame, text="Password:", bg="white", font=("Arial", 14)).pack(pady=5)
        self.password_entry = tk.Entry(self.login_frame, show="*", font=("Arial", 14))
        self.password_entry.pack(pady=5, ipady=6, ipadx=12, fill="x", padx=20)

        # Login Button
        self.login_button = tk.Button(self.login_frame, text="Login", command=self.login, bg="blue", fg="white", font=("Arial", 14, "bold"))
        self.login_button.pack(pady=15, ipadx=50, ipady=6)

        # Register Button (Bigger & More Visible)
        self.register_button = tk.Button(self.login_frame, text="Create an Account", command=self.register_user, bg="green", fg="white", font=("Arial", 12, "bold"))
        self.register_button.pack(pady=5, ipadx=20, ipady=6)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        print(f"Logging in with: {username} / {password}")  # Debugging

        try:
            response = APIClient.login(username, password)
            print(f"API Response: {response}")  # Debugging

            self.token = response.get("access_token")
            self.borrower_id = response.get("user_id")

            if self.token and self.borrower_id:
                messagebox.showinfo("Success", "Login successful!")

                # Destroy only the login frame, not the entire root window
                for widget in self.root.winfo_children():
                    widget.destroy()

                # Open Dashboard
                Dashboard(self.root, self.token, self.borrower_id)

            else:
                messagebox.showerror("Error", "Invalid login: Missing token or borrower_id")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Login failed: {e}")

    def register_user(self):
        email = self.username_entry.get()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please provide email and password.")
            return
        
        user_data = {
            "email": email,
            "password": password,
            "first_name": "FirstName",
            "last_name": "LastName",
            "role": "student"
        }

        try:
            APIClient.register(user_data)
            messagebox.showinfo("Success", "User registered! You can now login.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Registration failed: {e}")

# Run Application
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginRegister(root)
    root.mainloop()
