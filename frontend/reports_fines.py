import tkinter as tk
from tkinter import messagebox
from api_client import APIClient

class ReportsFines:
    @staticmethod
    def display_reports(root, data, borrower_id):
        reports_window = tk.Toplevel(root)
        reports_window.title("Reports and Fines")

        user_label = tk.Label(reports_window, text=f"User ID: {borrower_id}")
        user_label.pack()

        if "fines" in data:
            fines_label = tk.Label(reports_window, text="Fines:")
            fines_label.pack()

            for fine in data["fines"]:
                fine_text = f"Fine ID: {fine['id']}, Amount: {fine['amount']}, Paid: {fine['paid']}"
                tk.Label(reports_window, text=fine_text).pack()

        if "total" in data:
            total_label = tk.Label(reports_window, text=f"Total Paid: {data['total']['paid']}, Total Unpaid: {data['total']['unpaid']}")
            total_label.pack()
