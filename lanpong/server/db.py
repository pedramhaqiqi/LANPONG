import json
import threading
from pathlib import Path
import os
import re


class DB:
    def __init__(self, filename="users.json"):
        """
        Initialize the DB object.

        Args:
            filename (str): The name of the JSON file used for storage.
        """
        self.filename = filename
        self.lock = threading.Lock()
        self.path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), self.filename
        )
        self.users = self.load_db()

    def load_db(self):
        """
        Load the user data from the JSON file.

        Returns:
            list: List of user objects.
        """
        if not Path(self.path).is_file():
            return []
        with open(self.path, "r") as file:
            return json.load(file)

    def save_db(self):
        """
        Save the user data to the JSON file.
        """
        with open(self.path, "w") as file:
            json.dump(self.users, file, indent=2)

    def is_username_valid(self, username):
        """
        Check if the given username is unique in the user list.

        Args:
            username (str): The username to check.

        Returns:
            bool: True if the username is unique, False otherwise.
        """
        if username == "" or re.search(r"\s", username):
            return False

        for user in self.users:
            if user["username"] == username:
                return False
        return True

    def create_user(self, username, password, score=0):
        print("creating user")
        """
        Create a new user with sanitization and unique username checking.

        Args:
            username (str): The new username.
            password (str): The password for the new user.
            score (int): The initial score for the new user (default is 0).

        Raises:
            ValueError: If the username is not unique or if either username or password is empty.
        """
        if not username or not password:
            raise ValueError("Username and password are required.")

        with self.lock:
            if not self.is_username_valid(username):
                raise ValueError("Username already exists.")

            new_user = {
                "id": len(self.users) + 1,
                "username": username,
                "password": password,
                "score": score,
            }

            self.users.append(new_user)
            self.save_db()

    def update_user(self, user_id, new_data):
        """
        Update user information based on the user's ID.

        Args:
            user_id (int): The ID of the user to update.
            new_data (dict): A dictionary containing the new data to update for the user.

        Raises:
            ValueError: If the user with the specified ID is not found.
        """
        with self.lock:
            for user in self.users:
                if user["id"] == user_id:
                    user.update(new_data)
                    self.save_db()
                    return
            raise ValueError(f"User with ID {user_id} not found.")

    def login(self, username, password):
        """
        Attempt to authenticate a user with the provided username and password.

        Args:
            username (str): The username to authenticate.
            password (str): The password to authenticate.

        Returns:
            dict: User information if authentication is successful, None otherwise.
        """
        with self.lock:
            for user in self.users:
                if user["username"] == username and user["password"] == password:
                    return user
        return None


"""
# Example usage:
db = DB()

try:
    db.create_user('john_doe', 'password123', score=100)
    print(db.users)
    db.create_user('jane_doe', 'securepass', score=150)
    print(db.users)
    # Update user information
    db.update_user(1, {'score': 120})

    # Attempt to create a user with a non-unique username
    db.create_user('john_doe', 'newpassword', score=200)
    print(db.users)
except ValueError as e:
    print(f"Error: {e}")

# Print the current user list
print(db.users)
"""
