import json
import os
from people_class.user_class import User

class UserManager:
    """Handles storing and retrieving users from a JSON file."""
    def __init__(self, filepath="presistant_storage/users.json"):
        self.filepath = filepath
        self.users = []
        self.load_users()
    
    def load_users(self):
        """Load users from JSON file."""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                data = json.load(f)
                self.users = [User.from_dict(u) for u in data]
        else:
            self.users = []
    
    def save_users(self):
        """Save users to JSON file."""
        with open(self.filepath, "w") as f:
            json.dump([u.to_dict() for u in self.users], f, indent=4)
    
    def add_user(self, name, email):
        """Add a new user if not already existing."""
        new_user = User(name, email)
        if new_user not in self.users:
            self.users.append(new_user)
            self.save_users()
            print(f"✅ Added user: {new_user}")
        else:
            print(f"⚠️ User with email {email} already exists.")
    
    def list_users(self):
        """Print all users."""
        if not self.users:
            print("No users found.")
        for user in self.users:
            print(user)