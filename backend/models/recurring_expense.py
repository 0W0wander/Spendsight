"""Recurring expense model for budget tracking."""
from dataclasses import dataclass, field
from typing import List, Optional
import json
from pathlib import Path
import uuid


@dataclass
class RecurringExpense:
    """
    Represents a recurring expense that can be linked to transactions.
    
    A recurring expense can be linked to transactions using keywords (AND logic),
    similar to how auto-tagging rules work.
    """
    id: str
    name: str  # Display name (e.g., "Rent", "Car Insurance")
    amount: float  # Expected amount
    frequency: str = 'monthly'  # 'weekly' or 'monthly'
    keywords: List[str] = field(default_factory=list)  # Keywords to match transactions
    enabled: bool = True
    category: str = 'Other'  # Category for display purposes
    
    def matches(self, description: str) -> bool:
        """
        Check if this expense matches the given description.
        
        All keywords must be present (AND logic).
        Matching is case-insensitive.
        
        Args:
            description: The transaction description to check
            
        Returns:
            True if all keywords are found in the description
        """
        if not self.enabled or not self.keywords:
            return False
        
        desc_lower = description.lower()
        return all(keyword.lower() in desc_lower for keyword in self.keywords)
    
    def to_dict(self) -> dict:
        """Convert expense to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'amount': self.amount,
            'frequency': self.frequency,
            'keywords': self.keywords,
            'enabled': self.enabled,
            'category': self.category
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RecurringExpense':
        """Create expense from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data['name'],
            amount=float(data.get('amount', 0)),
            frequency=data.get('frequency', 'monthly'),
            keywords=data.get('keywords', []),
            enabled=data.get('enabled', True),
            category=data.get('category', 'Other')
        )


class RecurringExpenseEngine:
    """
    Engine for managing recurring expenses and linking them to transactions.
    """
    
    def __init__(self, storage_path: Path = None):
        """
        Initialize the expense engine.
        
        Args:
            storage_path: Path to store expenses persistently (JSON file)
        """
        self.expenses: List[RecurringExpense] = []
        self.storage_path = storage_path or Path(__file__).resolve().parent.parent.parent / 'data' / 'recurring_expenses.json'
        self._load_expenses()
    
    def _load_expenses(self):
        """Load expenses from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.expenses = [RecurringExpense.from_dict(e) for e in data.get('expenses', [])]
            except Exception as e:
                print(f"Error loading recurring expenses: {e}")
                self.expenses = []
        else:
            self.expenses = []
    
    def _save_expenses(self):
        """Save expenses to storage file."""
        try:
            # Ensure data directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'expenses': [e.to_dict() for e in self.expenses]
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving recurring expenses: {e}")
    
    def add_expense(self, name: str, amount: float, frequency: str = 'monthly', 
                   keywords: List[str] = None, category: str = 'Other') -> RecurringExpense:
        """
        Add a new recurring expense.
        
        Args:
            name: Display name for the expense
            amount: Expected amount
            frequency: 'weekly' or 'monthly'
            keywords: List of keywords for matching transactions
            category: Category for display
            
        Returns:
            The created RecurringExpense
        """
        expense = RecurringExpense(
            id=str(uuid.uuid4()),
            name=name,
            amount=amount,
            frequency=frequency,
            keywords=keywords or [],
            enabled=True,
            category=category
        )
        self.expenses.append(expense)
        self._save_expenses()
        return expense
    
    def update_expense(self, expense_id: str, name: str = None, amount: float = None,
                      frequency: str = None, keywords: List[str] = None, 
                      enabled: bool = None, category: str = None) -> Optional[RecurringExpense]:
        """
        Update an existing expense.
        
        Args:
            expense_id: ID of the expense to update
            name: New name (optional)
            amount: New amount (optional)
            frequency: New frequency (optional)
            keywords: New keywords list (optional)
            enabled: Enable/disable expense (optional)
            category: New category (optional)
            
        Returns:
            The updated RecurringExpense or None if not found
        """
        for expense in self.expenses:
            if expense.id == expense_id:
                if name is not None:
                    expense.name = name
                if amount is not None:
                    expense.amount = amount
                if frequency is not None:
                    expense.frequency = frequency
                if keywords is not None:
                    expense.keywords = keywords
                if enabled is not None:
                    expense.enabled = enabled
                if category is not None:
                    expense.category = category
                
                self._save_expenses()
                return expense
        return None
    
    def delete_expense(self, expense_id: str) -> bool:
        """
        Delete an expense by ID.
        
        Args:
            expense_id: ID of the expense to delete
            
        Returns:
            True if deleted, False if not found
        """
        for i, expense in enumerate(self.expenses):
            if expense.id == expense_id:
                del self.expenses[i]
                self._save_expenses()
                return True
        return False
    
    def get_expense(self, expense_id: str) -> Optional[RecurringExpense]:
        """Get an expense by ID."""
        for expense in self.expenses:
            if expense.id == expense_id:
                return expense
        return None
    
    def get_all_expenses(self) -> List[RecurringExpense]:
        """Get all expenses."""
        return self.expenses
    
    def get_expenses_by_frequency(self, frequency: str) -> List[RecurringExpense]:
        """Get expenses filtered by frequency."""
        return [e for e in self.expenses if e.frequency == frequency and e.enabled]
    
    def link_to_transactions(self, expense: RecurringExpense, transactions: list) -> int:
        """
        Link a recurring expense to matching transactions.
        
        Sets the recurrence field to 'Recurring' for all matching transactions.
        
        Args:
            expense: The recurring expense with keywords
            transactions: List of Transaction objects
            
        Returns:
            Number of transactions that were linked
        """
        if not expense.keywords:
            return 0
        
        linked_count = 0
        for transaction in transactions:
            if expense.matches(transaction.description):
                # Set recurrence to Recurring
                if hasattr(transaction, 'recurrence'):
                    transaction.recurrence = 'Recurring'
                    linked_count += 1
        
        return linked_count
    
    def link_all_expenses(self, transactions: list) -> int:
        """
        Link all recurring expenses to matching transactions.
        
        Args:
            transactions: List of Transaction objects
            
        Returns:
            Total number of transactions that were linked
        """
        total_linked = 0
        for expense in self.expenses:
            if expense.enabled and expense.keywords:
                total_linked += self.link_to_transactions(expense, transactions)
        return total_linked
    
    def find_matching_transactions(self, expense: RecurringExpense, transactions: list) -> list:
        """
        Find all transactions that match a recurring expense.
        
        Args:
            expense: The recurring expense with keywords
            transactions: List of Transaction objects
            
        Returns:
            List of matching transactions
        """
        if not expense.keywords:
            return []
        
        return [t for t in transactions if expense.matches(t.description)]
    
    def preview_matches(self, keywords: List[str], transactions: list, limit: int = 10) -> dict:
        """
        Preview which transactions would match given keywords.
        
        Args:
            keywords: List of keywords to match
            transactions: List of Transaction objects
            limit: Maximum number of sample matches to return
            
        Returns:
            Dictionary with match count and sample matches
        """
        if not keywords:
            return {'count': 0, 'samples': []}
        
        keywords_lower = [k.lower() for k in keywords]
        matches = []
        
        for t in transactions:
            desc_lower = t.description.lower()
            if all(kw in desc_lower for kw in keywords_lower):
                matches.append({
                    'description': t.description,
                    'amount': t.amount,
                    'date': t.transaction_date.strftime('%Y-%m-%d'),
                    'category': t.category
                })
        
        return {
            'count': len(matches),
            'samples': matches[:limit]
        }
    
    def get_totals_by_frequency(self) -> dict:
        """
        Get total expected amounts grouped by frequency.
        
        Returns:
            Dictionary with weekly and monthly totals
        """
        weekly_total = sum(e.amount for e in self.expenses if e.frequency == 'weekly' and e.enabled)
        monthly_total = sum(e.amount for e in self.expenses if e.frequency == 'monthly' and e.enabled)
        
        return {
            'weekly': round(weekly_total, 2),
            'monthly': round(monthly_total, 2),
            'monthly_equivalent': round(weekly_total * 4.33 + monthly_total, 2)  # Approximate monthly total
        }


# Global instance for the application
recurring_expense_engine = RecurringExpenseEngine()

