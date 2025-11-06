import json
import os
from typing import Dict, List, Union
from people_class.user_class import User
from people_class.group_class import Group

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
            print(f"Added user: {new_user}")
        else:
            print(f"User with email {email} already exists.")
    
    def list_users(self):
        """Print all users."""
        if not self.users:
            print("No users found.")
        for user in self.users:
            print(user)
    
    def get_user_by_email(self, email: str) -> Union[User, None]:
        """Retrieve a user by their email address."""
        return next((user for user in self.users if user.email == email), None)

class GroupManager:
    """Handles storing and retrieving Group objects (including expenses and debt state)."""
    def __init__(self, user_manager: UserManager, filepath="presistant_storage/groups.json"):
        self.filepath = filepath
        self.groups: Dict[str, Group] = {}
        self.user_manager = user_manager 
        self.load_groups()

    def add_group(self, group: Group):
        """Add a new group if the name is unique."""
        if group.name in self.groups:
            return False
        self.groups[group.name] = group
        self.save_groups()
        return True

    def get_group(self, name: str) -> Union[Group, None]:
        """Retrieve a group by name."""
        return self.groups.get(name)

    def list_groups(self):
        """Print all available group names."""
        if not self.groups:
            print("No groups available.")
            return False
        print("\n--- Available Groups ---")
        for name in self.groups.keys():
            print(f"- {name}")
        print("------------------------\n")
        return True
        
    def save_groups(self):
        """Save all groups to JSON file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump([g.to_dict() for g in self.groups.values()], f, indent=4)
        print("Groups saved successfully.")

    def load_groups(self):
        """Load all groups from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    self.groups = {
                        g['name']: Group.from_dict(g, self.user_manager) 
                        for g in data
                    }
                print(f"Loaded {len(self.groups)} groups.")
            except (IOError, json.JSONDecodeError, KeyError) as e:
                print(f"Error loading groups: {e}. Starting with an empty list.")
                self.groups = {}
        else:
            self.groups = {}