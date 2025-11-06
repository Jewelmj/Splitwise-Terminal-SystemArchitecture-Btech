from abc import ABC, abstractmethod
from people_class.user_class import User
from typing import List, Dict, Union, Tuple

class SplitStrategy(ABC):
    """
    Abstract Base Class for all expense split methods.
    Responsible for validating and calculating shares for an expense.
    """
    @abstractmethod
    def validate(self, amount: float, members: List[User], shares_data: Union[List[float], Dict[str, float]]) -> bool:
        """Validates if the shares data is correct for the total amount and members."""
        pass

    @abstractmethod
    def calculate_shares(self, amount: float, members: List[User], shares_data: Union[List[float], Dict[str, float]]) -> Dict[str, float]:
        """Calculates the final owed amount for each member."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Union[str, Dict[str, float]]]:
        """Serialization method for persistence."""
        pass
    
    @staticmethod
    @abstractmethod
    def from_dict(data: Dict) -> 'SplitStrategy':
        """Deserialization method for loading."""
        pass

class EqualSplit(SplitStrategy):
    """Splits the expense amount equally among all members."""
    
    def __init__(self, members: List[User]):
        self.split_type = "EQUAL"
        self.members_emails = [m.email for m in members] # for consistency.

    def validate(self, amount: float, members: List[User], shares_data=None) -> bool:
        """Always valid for equal split, as long as there is at least one member."""
        return len(members) > 0

    def calculate_shares(self, amount: float, members: List[User], shares_data=None) -> Dict[str, float]:
        """Calculates the equal share amount for each member."""
        if not members:
            return {}
        
        share_amount = round(amount / len(members), 2)
        total_calculated = share_amount * len(members)
        remainder = round(amount - total_calculated, 2)
        
        shares = {}
        for i, user in enumerate(members):
            final_share = share_amount
            if i < int(remainder * 100): # Distribute reminder.
                final_share += 0.01
            shares[user.email] = round(final_share, 2)

        if round(sum(shares.values()), 2) != amount:
             last_user_email = members[-1].email
             shares[last_user_email] = round(shares[last_user_email] + (amount - sum(shares.values())), 2)

        return shares

    def to_dict(self) -> Dict[str, str]:
        return {'type': self.split_type}
    
    @staticmethod
    def from_dict(data: Dict) -> 'EqualSplit':
        return EqualSplit(members=[])


class PercentageSplit(SplitStrategy):
    """Splits the expense amount based on provided percentages."""
    def __init__(self, percentages: Dict[str, float]):
        """
        Args:
            percentages (Dict[str, float]): A dictionary mapping user email to percentage (0-100).
        """
        self.split_type = "PERCENTAGE"
        self.percentages = percentages  # {user_email: percentage}
        
    def validate(self, amount: float, members: List[User], shares_data: Dict[str, float]) -> bool:
        """Validates that all percentages sum up to 100."""
        if not shares_data or not all(isinstance(v, (int, float)) for v in shares_data.values()):
            return False
        
        return abs(sum(shares_data.values()) - 100.0) < 1e-9

    def calculate_shares(self, amount: float, members: List[User], shares_data: Dict[str, float]) -> Dict[str, float]:
        """Calculates the share amount for each member based on their percentage."""
        shares = {}
        for email, percentage in shares_data.items():
            shares[email] = round(amount * (percentage / 100.0), 2)
        
        total_shares = round(sum(shares.values()), 2)
        if total_shares != amount:
            first_member_email = next(iter(shares_data))
            shares[first_member_email] = round(shares[first_member_email] + (amount - total_shares), 2)

        return shares
    
    def to_dict(self) -> Dict[str, Union[str, Dict[str, float]]]:
        return {'type': self.split_type, 'percentages': self.percentages}

    @staticmethod
    def from_dict(data: Dict) -> 'PercentageSplit':
        return PercentageSplit(data['percentages'])
    
def get_strategy_from_dict(data: Dict) -> SplitStrategy:
    split_type = data.get('type')
    if split_type == "EQUAL":
        return EqualSplit.from_dict(data)
    elif split_type == "PERCENTAGE":
        return PercentageSplit.from_dict(data)
    raise ValueError(f"Unknown SplitType: {split_type}")