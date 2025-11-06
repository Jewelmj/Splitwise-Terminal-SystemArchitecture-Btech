import unittest
import os
import json
import shutil

from people_class.user_class import User
from manager_class.manager import UserManager, GroupManager 
from transaction_class.debt_class import DebtRecord
from people_class.group_class import Group
from transaction_class.expense_class import Expense
from transaction_class.split_class import EqualSplit, PercentageSplit 

TEST_DIR = "test_persistence"
USER_FILE = os.path.join(TEST_DIR, "users.json")
GROUP_FILE = os.path.join(TEST_DIR, "groups.json")

class TestSplitSmart(unittest.TestCase):
    """
    Comprehensive test suite for the SplitSmart application classes.
    """
    
    def setUp(self):
        """
        Set up the environment before each test: 
        1. Ensure test directory exists.
        2. Create fresh instances of UserManager and GroupManager.
        """
        os.makedirs(TEST_DIR, exist_ok=True)
        if os.path.exists(USER_FILE):
            os.remove(USER_FILE)
        if os.path.exists(GROUP_FILE):
            os.remove(GROUP_FILE)

        self.user_manager = UserManager(USER_FILE)
        self.group_manager = GroupManager(self.user_manager, GROUP_FILE)

        self.u1 = User("Alice", "alice@test.com")
        self.u2 = User("Bob", "bob@test.com")
        self.u3 = User("Charlie", "charlie@test.com")

        self.user_manager.add_user(self.u1.name, self.u1.email)
        self.user_manager.add_user(self.u2.name, self.u2.email)
        self.user_manager.add_user(self.u3.name, self.u3.email)
        
        self.user_manager = UserManager(USER_FILE)
        
        self.alice = self.user_manager.get_user_by_email("alice@test.com")
        self.bob = self.user_manager.get_user_by_email("bob@test.com")
        self.charlie = self.user_manager.get_user_by_email("charlie@test.com")

        self.trip_group = Group("Trip 2024")
        self.trip_group.add_member(self.alice)
        self.trip_group.add_member(self.bob)
        self.trip_group.add_member(self.charlie)
        self.group_manager.add_group(self.trip_group)
        self.trip_group_name = "Trip 2024"

    def tearDown(self):
        """Clean up the test directory after each test."""
        try:
            shutil.rmtree(TEST_DIR)
        except OSError:
            pass

    def test_01_user_and_group_initialization(self):
        """Test user retrieval and basic group membership."""
        self.assertIsNotNone(self.alice, "Alice should be loaded by the user manager.")
        self.assertIn(self.bob.email, self.trip_group.members, "Bob should be a member of the group.")
        self.assertIsNotNone(self.group_manager.get_group(self.trip_group_name), "Group should be managed.")

    def test_02_equal_split_expense(self):
        """Test equal split for a single expense: $300 paid by Alice for 3 people."""
        # FIX: Added required 'shares_data' argument (300 / 3 = 100 per person)
        shares_data = {self.alice.email: 100.00, self.bob.email: 100.00, self.charlie.email: 100.00}
        expense = Expense(
            description="Hotel",
            amount=300.00,
            paid_by=self.alice,
            members=[self.alice, self.bob, self.charlie],
            split_strategy=EqualSplit([self.alice, self.bob, self.charlie]),
            shares_data=shares_data 
        )

        self.trip_group.add_expense(expense.to_dict())
        debts = self.trip_group.view_debt()

        self.assertEqual(len(debts), 2, "Debts should be 2 transactions (Bob->Alice, Charlie->Alice).")
        
        alice_debts = [d for d in debts if d.lender_email == self.alice.email]
        
        self.assertTrue(any(d.borrower_email == self.bob.email and d.amount == 100.00 for d in alice_debts), "Bob should owe Alice $100.00.")
        self.assertTrue(any(d.borrower_email == self.charlie.email and d.amount == 100.00 for d in alice_debts), "Charlie should owe Alice $100.00.")

    def test_03_debt_simplification(self):
        """Test simplification: A owes B $100, B owes C $100 -> A owes C $100."""
        
        # Original: Bob owes Alice $50
        e1 = Expense(
            description="E1", amount=100.00, paid_by=self.alice, members=[self.alice, self.bob],
            split_strategy=EqualSplit([self.alice, self.bob]), shares_data={self.alice.email: 50.0, self.bob.email: 50.0}
        )
        self.trip_group.add_expense(e1.to_dict())

        # Original: Charlie owes Bob $50
        # NOTE: The test file had duplicate expense definitions; keeping only the correct final ones.
        e2 = Expense(
            description="E2", amount=100.00, paid_by=self.bob, members=[self.bob, self.charlie],
            split_strategy=EqualSplit([self.bob, self.charlie]), shares_data={self.bob.email: 50.0, self.charlie.email: 50.0}
        )
        self.trip_group.add_expense(e2.to_dict())
        
        # Expected Net Result (Simplification): Charlie owes Alice $50
        debts = self.trip_group.view_debt()
        self.assertEqual(len(debts), 1, "Debts should be simplified to 1 transaction (Charlie->Alice $50.00).")
        self.assertEqual(debts[0].borrower_email, self.charlie.email)
        self.assertEqual(debts[0].lender_email, self.alice.email)
        self.assertEqual(debts[0].amount, 50.00)

    def test_04_settle_up(self):
        """Test recording a settlement and subsequent debt recalculation."""
        # FIX: Added required 'shares_data' argument (300 / 3 = 100 per person)
        shares_data = {self.alice.email: 100.00, self.bob.email: 100.00, self.charlie.email: 100.00}
        expense = Expense(
            description="Hotel", amount=300.00, paid_by=self.alice, members=[self.alice, self.bob, self.charlie],
            split_strategy=EqualSplit([self.alice, self.bob, self.charlie]),
            shares_data=shares_data
        )
        self.trip_group.add_expense(expense.to_dict())
        
        self.trip_group.settle_up(self.bob, self.alice, 50.00)
        debts = self.trip_group.view_debt()
        
        self.assertEqual(len(debts), 2, "Debts should remain 2 after partial settlement.")
        
        bob_debt = next(d for d in debts if d.borrower_email == self.bob.email)
        charlie_debt = next(d for d in debts if d.borrower_email == self.charlie.email)
        
        self.assertEqual(bob_debt.amount, 50.00, "Bob's remaining debt should be $50.00.")
        self.assertEqual(charlie_debt.amount, 100.00, "Charlie's debt should remain $100.00.")
        self.assertTrue(all(d.lender_email == self.alice.email for d in debts), "Alice should be the sole lender.")

    def test_05_persistence(self):
        """Test if User and Group data can be saved and reloaded."""
        self.group_manager.save_groups()
        new_user_manager = UserManager(USER_FILE)
        new_group_manager = GroupManager(new_user_manager, GROUP_FILE)

        self.assertIsNotNone(new_user_manager.get_user_by_email("alice@test.com"))
        self.assertEqual(len(new_user_manager.users), 3)
        
        reloaded_group = new_group_manager.get_group(self.trip_group_name)
        self.assertIsNotNone(reloaded_group)
        self.assertEqual(len(reloaded_group.members), 3)

        # FIX: Added required 'shares_data' argument (90 / 3 = 30 per person)
        shares_data = {self.alice.email: 30.00, self.bob.email: 30.00, self.charlie.email: 30.00}
        expense = Expense(
            description="Dinner", amount=90.00, paid_by=self.alice, members=[self.alice, self.bob, self.charlie],
            split_strategy=EqualSplit([self.alice, self.bob, self.charlie]),
            shares_data=shares_data
        )
        self.trip_group.add_expense(expense.to_dict())
        self.group_manager.save_groups()
        
        final_user_manager = UserManager(USER_FILE)
        final_group_manager = GroupManager(final_user_manager, GROUP_FILE)
        final_group = final_group_manager.get_group(self.trip_group_name)
        
        debts = final_group.view_debt()
        self.assertEqual(len(debts), 2, "Debts should be 2 after loading with an expense (Bob->Alice, Charlie->Alice).")
        self.assertTrue(all(d.amount == 30.00 for d in debts), "Debt amounts should be $30.00.")


if __name__ == '__main__':
    print("Running Test Suite for SplitSmart...")
    print("-----------------------------------")
    try:
        unittest.main(argv=['first-arg-is-ignored'], exit=False)
    except Exception as e:
        print(f"\nFATAL ERROR: Test runner encountered an exception: {e}")
    finally:
        print("\nTest run finished. Check output for 'OK' or 'FAILURES'.")