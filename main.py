import os
from people_class.user_class import User
from people_class.group_class import Group
from transaction_class.expense_class import Expense
from transaction_class.split_class import EqualSplit, PercentageSplit 
from manager_class.manager import UserManager, GroupManager 
from typing import Union

def get_group_selection(group_manager: GroupManager) -> Union[Group, None]:
    """Prompts the user to select an existing group."""
    if not group_manager.list_groups():
        return None
    group_name = input("Enter the name of the group: ")
    group = group_manager.get_group(group_name)
    if not group:
        print("Group not found.")
    return group

def get_user_selection(user_manager: UserManager, prompt: str) -> Union[User, None]:
    """Prompts the user to select an existing user by email."""
    user_manager.list_users()
    user_email = input(prompt)
    user = user_manager.get_user_by_email(user_email)
    if not user:
        print(f"User with email '{user_email}' not found.")
    return user

def handle_create_group(user_manager: UserManager, group_manager: GroupManager):
    """Handles the creation of a new group with selected members."""
    group_name = input("Enter the name for the new group: ")
    
    user_manager.list_users()
    email_str = input("Enter a comma-separated list of member emails (e.g., a@mail.com, b@mail.com):\n")
    email_list = [e.strip() for e in email_str.split(',') if e.strip()]
    
    if not email_list:
        print("Group must have members.")
        return

    group = Group(group_name)
    found_all = True
    for email in email_list:
        user = user_manager.get_user_by_email(email)
        if user:
            group.add_member(user)
        else:
            print(f"User with email '{email}' not found. Cannot add to group.")
            found_all = False
            
    if found_all and group.members:
        group_manager.add_group(group)
    elif not found_all:
        print("Group creation failed due to missing users.")
    else:
        print("Cannot create group with zero valid members.")


def handle_add_expense(user_manager: UserManager, group_manager: GroupManager):
    """Handles adding a new expense, currently defaulted to Equal Split."""
    group = get_group_selection(group_manager)
    if not group:
        return
    
    members_list = list(group.members.values())
    if len(group.members) < 1:
        print("Group must have at least one member to record an expense.")
        return

    description = input("Enter expense description: ")
    try:
        amount = float(input("Enter total expense amount: $"))
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("Invalid or non-positive amount.")
        return

    paid_by = get_user_selection(user_manager, "Enter email of the user who PAID: ")
    if not paid_by or paid_by.email not in group.members:
        print("Payer must be a member of the selected group.")
        return

    split_type = input("Enter spit type (EQUAL or PERCENTAGE):").upper()
    strategy = None
    shares_data = None
    
    if split_type == "EQUAL":
        strategy = EqualSplit(members_list)
        # For EqualSplit, we calculate the exact monetary share for each user
        share = round(amount / len(members_list), 2)
        shares_data = {member.email: share for member in members_list}
        
    elif split_type == "PERCENTAGE":
        strategy = PercentageSplit(members_list)
        percentages = {}
        total_percentage = 0.0
        
        print("\nEnter percentage share for each member (must sum to 100):")
        for member in members_list:
            while True:
                try:
                    percent = float(input(f"  {member.name} ({member.email}) gets what percentage? "))
                    if percent < 0:
                        raise ValueError
                    percentages[member.email] = percent
                    total_percentage += percent
                    break
                except ValueError:
                    print("Invalid percentage. Please enter a non-negative number.")

        if abs(total_percentage - 100.0) > 0.01:
            print(f"Error: Percentages sum to {total_percentage:.2f}%. They must sum to 100%.")
            return
            
        shares_data = percentages # shares_data for PercentageSplit is the dict of percentages
        
    else:
        print("Invalid split type selected.")
        
    try:
        expense = Expense(
            description=description,
            amount=amount,
            paid_by=paid_by,
            members=list(group.members.values()),
            split_strategy=strategy,
            shares_data=shares_data
        )
        group.add_expense(expense.to_dict())
        group_manager.save_groups()
        
    except ValueError as e:
        print(f"Failed to add expense: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def handle_view_debts(group_manager: GroupManager):
    """Displays the simplified debt summary for a selected group."""
    group = get_group_selection(group_manager)
    if not group:
        return
    
    print(group.get_summary())


def handle_settle_up(user_manager: UserManager, group_manager: GroupManager):
    """Records a cash payment (settlement) between two users in a group."""
    group = get_group_selection(group_manager)
    if not group:
        return
        
    payer = get_user_selection(user_manager, "Enter email of the user who IS PAYING (borrower): ")
    if not payer or payer.email not in group.members:
        print("Payer must be a member of the group.")
        return
        
    recipient = get_user_selection(user_manager, "Enter email of the user who IS RECEIVING (lender): ")
    if not recipient or recipient.email not in group.members:
        print("Recipient must be a member of the group.")
        return
        
    if payer.email == recipient.email:
        print("Cannot settle up with yourself.")
        return

    try:
        amount = float(input("Enter settlement amount: $"))
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("Invalid or non-positive amount.")
        return
        
    group.settle_up(payer, recipient, amount)
    group_manager.save_groups()

def handle_save_load_data(user_manager: UserManager, group_manager: GroupManager):
    """Saves all current data."""
    user_manager.save_users()
    group_manager.save_groups()
    print("All user and group data saved.")

print("Welcome to SplitSmart,")
os.makedirs("presistant_storage", exist_ok=True)
user_manager = UserManager("presistant_storage/users.json")
group_manager = GroupManager(user_manager, "presistant_storage/groups.json")

while True:
    user_input = input("SplitSmart Menu: \n1. Add User \n2. Create Group \n3. Add Expense \n4. View Debts \n5. Settle Up \n6. Save and Exit\n:")
    
    if user_input == "1":
        user_name = input("enter name:")
        user_emal = input("enter email:")
        user_manager.add_user(user_name, user_emal)
        
    elif user_input == "2":
        handle_create_group(user_manager, group_manager)
        
    elif user_input == "3":
        handle_add_expense(user_manager, group_manager)
        
    elif user_input == "4":
        handle_view_debts(group_manager)
        
    elif user_input == "5":
        handle_settle_up(user_manager, group_manager)

    elif user_input == "6":
        handle_save_load_data(user_manager, group_manager)
        print("Thank you for using SplitSmart!")
        break
        
    else:
        print("Invalid input \n\n")