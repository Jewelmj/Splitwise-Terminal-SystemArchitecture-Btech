# SplitSmart 💸

A Python-based CLI app to manage shared expenses, calculate group debts, and record settlements — inspired by apps like Splitwise.

---

## 🧩 Architecture Overview

SplitSmart uses an **Object-Oriented modular structure**:

| Module | Purpose |
|--------|----------|
| `user_class.py` | Defines `User` entities |
| `group_class.py` | Manages members, expenses, and debts in a group |
| `expense_class.py` | Represents a single expense with a `SplitStrategy` |
| `split_class.py` | Strategy pattern for Equal or Percentage splits |
| `debt_class.py` | Handles debt simplification and settlement |
| `manager.py` | Persistence layer for users and groups (JSON) |
| `main.py` | CLI controller and app entry point |

---

## 🧱 Design Decisions

1. **OOP Principles**  
   Each real-world concept (User, Group, Expense) is modeled as a class.  
   The relationships mirror actual group dynamics (composition and aggregation).

2. **Strategy Pattern**  
   The `SplitStrategy` abstract class defines the splitting logic.  
   - `EqualSplit` – divides equally  
   - `PercentageSplit` – divides based on custom ratios

3. **Persistence via JSON**  
   Managers read/write from `users.json` and `groups.json`.  
   No database is required, keeping it lightweight and portable.

4. **Debt Simplification Algorithm**  
   `DebtTracker` uses a **greedy approach** to minimize transactions — simplifying all member balances into minimal debt records.

---

## 🧩 Assumptions

- Each user is uniquely identified by email.  
- All splits must sum to the total amount (for Equal or Percentage splits).  
- Groups and users are stored persistently in JSON.  
- Expenses are immutable once added (ledger-style tracking).  

---

## 🧮 How to Run

1. Clone or extract the repository.
2. Ensure Python 3.8+ is installed.
3. Run the app:

   ```bash
   python main.py
