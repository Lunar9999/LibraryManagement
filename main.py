import tkinter as tk
from login_register import LoginRegister
from styles import configure_styles

def main():
    root = tk.Tk()
    configure_styles(root)
    app = LoginRegister(root)
    root.mainloop()

if __name__ == "__main__":
    main()
