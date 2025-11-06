from people_class.user_class import User
from transaction_class.split_class import SplitStrategy, get_strategy_from_dict
from typing import List, Dict, Union

class Expense:
    """
    Represents a single transaction in a group.
    
    Attributes from UML:
        description (str)
        amount (float)
        paidBy (User)
        splitType (SplitStrategy object)
        shares (Dict[str, float]): {user_email: amount_owed}
    """
    def __init__(self, description: str, amount: float, paid_by: User, members: List[User], split_strategy: SplitStrategy, shares_data: Union[List[float], Dict[str, float]]):
        
        if not split_strategy.validate(amount, members, shares_data):
            raise ValueError(f"Invalid split configuration for {split_strategy.split_type} split. Total shares must match the amount or percentages must sum to 100.")
            
        self.description = description
        self.amount = amount
        self.paid_by_email = paid_by.email
        self.split_strategy = split_strategy
        self.shares = self.calculate_shares(amount, members, shares_data)

    def __str__(self):
        return f"Expense: {self.description} (${self.amount:.2f} paid by {self.paid_by_email})"

    def calculate_shares(self, amount: float, members: List[User], shares_data: Union[List[float], Dict[str, float]]) -> Dict[str, float]:
        """
        (Corresponds to calculateShares() in UML)
        Delegates the calculation to the specific SplitStrategy.
        """
        return self.split_strategy.calculate_shares(amount, members, shares_data)

    def validate_split(self, members: List[User], shares_data: Union[List[float], Dict[str, float]]) -> bool:
        """
        (Corresponds to validateSplit() in UML)
        Delegates the validation to the specific SplitStrategy.
        """
        return self.split_strategy.validate(self.amount, members, shares_data)

    def get_share(self, user: User) -> float:
        """
        (Corresponds to getShare() in UML)
        Returns the amount owed by a specific user.
        """
        return self.shares.get(user.email, 0.0)

    def display_expense(self) -> None:
        """
        (Corresponds to displayExpense() in UML)
        Prints a detailed summary of the expense.
        """
        print(f"\n--- Expense: {self.description} ---")
        print(f"Amount: ${self.amount:.2f}")
        print(f"Paid By: {self.paid_by_email}")
        print(f"Split Type: {self.split_strategy.split_type}")
        print("Shares:")
        for email, share in self.shares.items():
            print(f"  - {email} owes: ${share:.2f}")
        print("----------------------------\n")
    
    def to_dict(self) -> Dict:
        """Convert expense to dictionary for JSON serialization."""
        return {
            'description': self.description,
            'amount': self.amount,
            'paid_by_email': self.paid_by_email,
            'split_strategy': self.split_strategy.to_dict(),
            'shares': self.shares
        }

    @classmethod
    def from_dict(cls, data: Dict, user_manager, group_members: List[User]):
        """Create an Expense object from a dictionary."""
        strategy = get_strategy_from_dict(data['split_strategy'])
        paid_by_user = user_manager.get_user_by_email(data['paid_by_email'])

        temp_expense = cls.__new__(cls)
        temp_expense.description = data['description']
        temp_expense.amount = data['amount']
        temp_expense.paid_by_email = data['paid_by_email']
        temp_expense.split_strategy = strategy
        temp_expense.shares = data['shares']
        
        return temp_expense