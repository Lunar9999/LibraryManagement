import tkinter as tk
from tkinter import messagebox
from api_client import APIClient
import requests
from tkinter import ttk  

class BookManagement:
    @staticmethod
    def add_book(token, book_data):
        if not token:
            messagebox.showerror("Error", "You must be logged in to add a book.")
            return
        
        try:
            APIClient.add_book(token, book_data)
            messagebox.showinfo("Success", "Book added successfully!")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to add book: {e}")

    @staticmethod
    def borrow_book(token, book_id, borrower_id):
        if not token or not borrower_id:
            messagebox.showerror("Error", "You must be logged in to borrow a book.")
            return

        try:
            APIClient.borrow_book(token, book_id, borrower_id)
            messagebox.showinfo("Success", "Book borrowed successfully!")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to borrow book: {e}")

    @staticmethod
    def return_book(token, book_id, borrower_id):
        if not token or not borrower_id:
            messagebox.showerror("Error", "You must be logged in to return a book.")
            return

        try:
            APIClient.return_book(token, book_id, borrower_id)
            messagebox.showinfo("Success", "Book returned successfully!")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to return book: {e}")

    @staticmethod
    def show_borrowed_books(root, borrows):
        borrowed_window = tk.Toplevel(root)
        borrowed_window.title("Borrowed Books")

        borrowed_tree = ttk.Treeview(borrowed_window, columns=("Borrow ID", "Book Title", "Borrow Date", "Due Date", "Returned"), show="headings")
        for col in ["Borrow ID", "Book Title", "Borrow Date", "Due Date", "Returned"]:
            borrowed_tree.heading(col, text=col)
        borrowed_tree.pack(pady=10)

        for borrow in borrows:
            borrowed_tree.insert("", "end", values=(
                borrow.get("id"),  # Borrow ID
                borrow.get("borrowed_book"),  # Book Title
                borrow.get("borrow_date"),  # Borrow Date
                borrow.get("due_date"),  # Due Date
                "Yes" if borrow.get("is_returned") else "No"  # Returned Status
            ))
