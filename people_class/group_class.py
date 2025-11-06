from people_class.user_class import User
from transaction_class.debt_class import DebtTracker, SettlementRecord, DebtRecord
from typing import List, Dict, Any, Union

class Group:
    """
    Represents a group in SplitSmart, managing members, expenses, and debt.
    
    Attributes:
        name (str): The name of the group.
        members (dict): A dictionary mapping user email to User objects.
        expenses (list): A list of serialized Expense dictionaries (the immutable ledger).
        debt_tracker (DebtTracker): The service responsible for debt calculation and simplification.
    """
    def __init__(self, name: str):
        self.name = name
        self.members: Dict[str, User] = {}  
        self.expenses: List[Dict] = [] 
        self.debt_tracker = DebtTracker()
        
    def __str__(self):
        return f"Group: {self.name} ({len(self.members)} members)"
    
    def __eq__(self, other):
        """Groups are considered equal if they have the same name."""
        if isinstance(other, Group):
            return self.name == other.name
        return False

    def add_member(self, user: User):
        """Add a user to the group's members list."""
        if user.email not in self.members:
            self.members[user.email] = user
            print(f"User {user.name} added to group {self.name}.")
        else:
            print(f"User {user.name} is already a member of group {self.name}.")

    def add_expense(self, expense_data: Dict):
        """
        Add an expense to the group's ledger and update the debt tracker.
        
        Args:
            expense_data (Dict): A serialized dictionary of the Expense object.
        """
        self.expenses.append(expense_data)
        self.update_debts()
        
        print(f"Added expense '{expense_data['description']}' of ${expense_data['amount']} to group {self.name}.")

    def view_debt(self) -> List[DebtRecord]:
        """
        (Corresponds to viewDebt() in UML)
        Returns the simplified list of outstanding debts.
        """
        return self.debt_tracker.getDebts()

    def settle_up(self, payer: User, recipient: User, amount: float):
        """
        (Corresponds to settleUp() in UML)
        Records a cash payment and updates the debt tracker.
        """
        self.debt_tracker.settleDebts(payer.email, recipient.email, amount)
        self.update_debts()
        
        print(f"Settlement recorded: {payer.name} paid ${amount:.2f} to {recipient.name} in group {self.name}.")
        
    def update_debts(self):
        """
        Internal method to trigger the DebtTracker to run its full calculation/simplification.
        This must be called after adding an expense or recording a settlement.
        """
        self.debt_tracker.updateDebts(self.expenses, self.members)


    def get_summary(self) -> str:
        """
        (Corresponds to getSummary() in UML)
        Get a summary of all outstanding debts and total expenses in the group.
        """
        total_expenses = sum(e.get('amount', 0.0) for e in self.expenses)
        
        summary = [f"\n--- Summary for Group: {self.name} ---"]
        summary.append(f"Total members: {len(self.members)}")
        summary.append(f"Total expenses recorded: ${total_expenses:.2f}")
        summary.append("\nOUTSTANDING DEBTS (Simplified):")

        debts = self.view_debt()
        if not debts:
            summary.append("  - All settled up!")
        else:
            for debt in debts:
                borrower_name = self.members.get(debt.borrower_email, debt.borrower_email).name
                lender_name = self.members.get(debt.lender_email, debt.lender_email).name
                summary.append(f"  - {borrower_name} owes {lender_name} ${debt.amount:.2f}")
        
        return "\n".join(summary)

    def to_dict(self):
        """Convert group to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'members': [user.to_dict() for user in self.members.values()],
            'expenses': self.expenses, 
            'debt_tracker': self.debt_tracker.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], user_manager):
        """
        Create a Group object from a dictionary.
        Requires a user_manager to fetch full User objects by email for consistency.
        """
        group = cls(data['name'])
        
        for user_data in data.get('members', []):
            user = user_manager.get_user_by_email(user_data['email'])
            if user:
                group.members[user.email] = user
            
        group.expenses = data.get('expenses', [])

        tracker_data = data.get('debt_tracker', {})
        group.debt_tracker = DebtTracker.from_dict(tracker_data)
        
        group.update_debts()
        
        return group