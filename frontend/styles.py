from tkinter import ttk

def configure_styles(root):
    style = ttk.Style(root)
    style.configure("TFrame", background="white")
    style.configure("TLabel", background="white", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 12), padding=10)
    style.configure("TEntry", font=("Arial", 12), padding=5)
    style.configure("Treeview", font=("Arial", 12), rowheight=25)
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

