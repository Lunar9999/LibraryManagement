import requests

BASE_URL = "http://127.0.0.1:5000"

class APIClient:
    @staticmethod
    def login(email, password):
        response = requests.post(f"{BASE_URL}/login", json={"email": email, "password": password})
        response.raise_for_status()
        return response.json()

    @staticmethod
    def register(user_data):
        response = requests.post(f"{BASE_URL}/register", json=user_data)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def fetch_books(token, filters=None):
        response = requests.get(f"{BASE_URL}/books", headers={"Authorization": f"Bearer {token}"}, params=filters)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def borrow_book(token, book_id, borrower_id):
        response = requests.post(f"{BASE_URL}/borrow-book", json={"book_id": book_id, "borrower_id": borrower_id}, 
        headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()

    @staticmethod
    def return_book(token, borrow_id):
        response = requests.post(
            f"{BASE_URL}/return-book",
            json={"borrow_id": borrow_id},  # Send borrow_id
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def fetch_borrowed_books(token):
        try:
            response = requests.get(
                f"{BASE_URL}/borrows",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            data = response.json()
            print("Backend Response:", data)  # Debug: Print the raw response
            return data                                       #.get("borrows", [])  # Extract the "borrows" list
        except requests.exceptions.RequestException as e:
            print(f"Error fetching borrowed books: {e}")
            return None

    @staticmethod
    def add_book(token, book_data):
        """Send a POST request to add a book and return the response object."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(f"{BASE_URL}/books", json=book_data, headers=headers)
        return response  # ✅ Return the full Response object, NOT response.json()

    @staticmethod
    def get_user_reports(user_id, token):
        try:
            # Fetch fines for the specific user
            response = requests.get(
                f"{BASE_URL}/fines-report",
                headers={"Authorization": f"Bearer {token}"},
                params={"user_id": user_id}  # Add this parameter if your backend supports it
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching fines report: {e}")
            return None
