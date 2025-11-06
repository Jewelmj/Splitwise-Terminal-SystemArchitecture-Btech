class User:
    """Represents a user in the SplitSmart application."""
    def __init__(self, name, email):
        """
        Initialize a User.
        
        Args:
            name (str): User's name
            email (str): User's email address
        """
        self.name = name
        self.email = email
        self.balance = 0.0  # Overall balance
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def __repr__(self):
        return f"User(name='{self.name}', email='{self.email}')"
    
    def __eq__(self, other):
        if isinstance(other, User):
            return self.email == other.email
        return False
    
    def __hash__(self):
        return hash(self.email)
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'email': self.email,
            'balance': self.balance
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create user from dictionary."""
        user = cls(data['name'], data['email'])
        user.balance = data.get('balance', 0.0)
        return user