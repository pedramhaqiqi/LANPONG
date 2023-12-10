import json
import threading
from pathlib import Path
import os


class DB:
    def __init__(self, filename="users.json"):
        """
        Initialize the DB object.

        Args:
            filename (str): The name of the JSON file used for storage.
        """
        self.filename = filename
        self.lock = threading.Lock()
        self.users = self.load_db()

    def load_db(self):
        """
        Load the user data from the JSON file.

        Returns:
            list: List of user objects.
        """
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.filename)
        if not Path(path).is_file():
            return []
        with open(path, "r") as file:
            return json.load(file)

    def save_db(self):
        """
        Save the user data to the JSON file.
        """
        with open(self.filename, "w") as file:
            json.dump(self.users, file, indent=2)

    def is_unique_username(self, username):
        """
        Check if the given username is unique in the user list.

        Args:
            username (str): The username to check.

        Returns:
            bool: True if the username is unique, False otherwise.
        """
        for user in self.users:
            if user["username"] == username:
                return False
        return True

    def create_user(self, username, password, score=0):
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
            if not self.is_unique_username(username):
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

    def get_top_users(self, num):
        """
        Get the top users based on their score.

        Args:
            num (int): The number of users to return.

        Returns:
            list: A list of the top users.
        """
        with self.lock:
            return sorted(self.users, key=lambda x: x["score"], reverse=True)[:num]


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