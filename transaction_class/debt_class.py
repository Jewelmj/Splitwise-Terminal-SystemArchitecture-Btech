import collections
from typing import List, Dict, Union, Any

NetBalances = Dict[str, float]

class DebtRecord:
    """
    Represents a single, simplified, net debt between two users.
    (Who Owes Whom)
    """
    def __init__(self, borrower_email: str, lender_email: str, amount: float):
        if amount <= 0:
            raise ValueError("Debt amount must be positive.")
            
        self.borrower_email = borrower_email
        self.lender_email = lender_email
        self.amount = round(amount, 2)
        
    def __str__(self):
        return f"{self.borrower_email} owes {self.lender_email} ${self.amount:.2f}"
    
    def to_dict(self) -> Dict[str, Union[str, float]]:
        return {
            'borrower_email': self.borrower_email,
            'lender_email': self.lender_email,
            'amount': self.amount,
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'DebtRecord':
        return cls(data['borrower_email'], data['lender_email'], data['amount'])


class SettlementRecord:
    """
    Represents an external cash payment used to settle a debt.
    (This is essentially a manual 'negative' expense)
    """
    def __init__(self, payer_email: str, recipient_email: str, amount: float):
        if amount <= 0:
            raise ValueError("Settlement amount must be positive.")
            
        self.payer_email = payer_email
        self.recipient_email = recipient_email
        self.amount = round(amount, 2)
        
    def to_dict(self) -> Dict[str, Union[str, float]]:
        return {
            'payer_email': self.payer_email,
            'recipient_email': self.recipient_email,
            'amount': self.amount,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SettlementRecord':
        return cls(data['payer_email'], data['recipient_email'], data['amount'])

class DebtTracker:
    """
    Manages the calculation, simplification, and settlement of debts for a group.
    
    Uses DebtRecord and SettlementRecord for internal state management.
    """
    
    def __init__(self):
        self.settlements: List[SettlementRecord] = [] 
        self.current_simplified_debts: List[DebtRecord] = []

    def _calculate_net_balances(self, expenses: List[Dict], members: Dict[str, Any]) -> NetBalances:
        """
        Calculates the net balance for every member based on all expenses and settlements.
        """
        balances = collections.defaultdict(float)
        member_emails = members.keys()

        for expense in expenses:
            paid_by_email = expense['paid_by_email']
            amount = expense['amount']
            shares = expense['shares']
            
            if paid_by_email in member_emails:
                balances[paid_by_email] += amount
            
            for borrower_email, share_amount in shares.items():
                if borrower_email in member_emails:
                    balances[borrower_email] -= share_amount

        for settlement in self.settlements:
            if settlement.payer_email in member_emails:
                balances[settlement.payer_email] += settlement.amount
            if settlement.recipient_email in member_emails:
                balances[settlement.recipient_email] -= settlement.amount
                
        return {email: round(balance, 2) for email, balance in balances.items() if abs(balance) > 0.01}


    def _simplify_debts(self, net_balances: NetBalances) -> List[DebtRecord]:
        """
        Uses a greedy algorithm to simplify the debt graph based on net balances, 
        returning a list of DebtRecord objects.
        """
        simplified_debts: List[DebtRecord] = []
        
        lenders = {email: balance for email, balance in net_balances.items() if balance > 0}
        borrowers = {email: -balance for email, balance in net_balances.items() if balance < 0}

        lender_list = sorted(lenders.items(), key=lambda item: item[1], reverse=True)
        borrower_list = sorted(borrowers.items(), key=lambda item: item[1], reverse=True)

        while lender_list and borrower_list:
            
            lender_email, lender_amount = lender_list.pop(0)
            borrower_email, borrower_amount = borrower_list.pop(0)

            payment_amount = min(lender_amount, borrower_amount)

            if payment_amount > 0.01:
                simplified_debts.append(DebtRecord(
                    borrower_email=borrower_email,
                    lender_email=lender_email,
                    amount=payment_amount
                ))

            lender_remaining = round(lender_amount - payment_amount, 2)
            borrower_remaining = round(borrower_amount - payment_amount, 2)
            
            if lender_remaining > 0.01:
                lender_list.append((lender_email, lender_remaining))
                lender_list.sort(key=lambda item: item[1], reverse=True)
                
            if borrower_remaining > 0.01:
                borrower_list.append((borrower_email, borrower_remaining))
                borrower_list.sort(key=lambda item: item[1], reverse=True)

        return simplified_debts

    def updateDebts(self, group_expenses: List[Dict], group_members: Dict[str, Any]):
        """
        Recalculates the entire simplified debt graph based on current expenses and settlements.
        """
        net_balances = self._calculate_net_balances(group_expenses, group_members)
        self.current_simplified_debts = self._simplify_debts(net_balances)
        
    def settleDebts(self, payer_email: str, recipient_email: str, amount: float):
        """
        Records an external cash payment, using the new SettlementRecord class.
        """
        self.settlements.append(SettlementRecord(
            payer_email=payer_email, 
            recipient_email=recipient_email, 
            amount=amount
        ))

    def getDebts(self) -> List[DebtRecord]:
        """
        Returns the most recently calculated and simplified list of outstanding debts.
        """
        return self.current_simplified_debts

    def to_dict(self) -> Dict:
        """
        Converts DebtTracker state (including the new classes) to dictionary for JSON serialization.
        """
        return {
            'settlements': [s.to_dict() for s in self.settlements],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'DebtTracker':
        """
        Creates DebtTracker from dictionary, recreating SettlementRecord objects.
        """
        tracker = cls()
        tracker.settlements = [SettlementRecord.from_dict(s) for s in data.get('settlements', [])]
        return tracker