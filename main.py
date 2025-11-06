from people_class.user_class import User
from transaction_class import *
from manager_class.manager import UserManager

print("Welcome to split wise,")
user_manager = UserManager("presistant_storage/users.json")

while True:
    user_input = input("SplitSmart Menu: \n1. Add User \n2. Create Group \n3. Add Expense \n4. View Debts \n5. Settle Up \n6. Save / Load Data \n7. Exit")
    if user_input == "1":
        user_name = input("enter name:")
        user_emal = input("enter email:")
        user_manager.add_user(user_name, user_emal)
    elif user_input == "7":
        user_manager.save_users()
        print("thank you!")
        break
    else:
        print("Invalid input \n\n")