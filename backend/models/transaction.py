"""Transaction data model."""
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


# Expense Type Constants
class ExpenseType:
    """Fixed vs Variable expense classification."""
    FIXED = "Fixed"
    VARIABLE = "Variable"
    INCOME = "Income"
    UNKNOWN = "Unknown"


class NecessityLevel:
    """Essential vs Discretionary classification (50/30/20 rule)."""
    NEEDS = "Needs"          # 50% - Essential expenses
    WANTS = "Wants"          # 30% - Discretionary spending
    SAVINGS = "Savings"      # 20% - Financial goals
    INCOME = "Income"
    UNKNOWN = "Unknown"


class RecurrenceType:
    """Subscription and recurring payment classification."""
    SUBSCRIPTION = "Subscription"      # Recurring digital/service subscriptions
    RECURRING = "Recurring"            # Regular but non-subscription (rent, utilities)
    ONE_TIME = "One-time"              # Single purchases
    INCOME = "Income"
    UNKNOWN = "Unknown"


class SpendingCategory:
    """High-level spending category for budgeting."""
    HOUSING = "Housing"
    TRANSPORTATION = "Transportation"
    FOOD = "Food"
    UTILITIES = "Utilities"
    HEALTHCARE = "Healthcare"
    INSURANCE = "Insurance"
    DEBT = "Debt Payment"
    SAVINGS_INVESTMENT = "Savings & Investment"
    PERSONAL = "Personal Care"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    EDUCATION = "Education"
    GIFTS_DONATIONS = "Gifts & Donations"
    TRAVEL = "Travel"
    FEES = "Fees & Charges"
    INCOME = "Income"
    TRANSFER = "Transfer"
    OTHER = "Other"


@dataclass
class Transaction:
    """Represents a financial transaction with multi-dimensional classification."""
    
    transaction_date: datetime
    post_date: datetime
    description: str
    amount: float
    category: str
    bank: str  # 'chase' or 'discover'
    type: Optional[str] = None  # 'Sale', 'Payment', 'Return', etc.
    memo: Optional[str] = None
    
    # Enhanced classification fields
    expense_type: str = field(default=ExpenseType.UNKNOWN)      # Fixed/Variable (for recurring only)
    necessity: str = field(default=NecessityLevel.UNKNOWN)       # Needs/Wants/Savings
    recurrence: str = field(default=RecurrenceType.UNKNOWN)      # Subscription/Recurring/One-time
    budget_category: str = field(default=SpendingCategory.OTHER) # High-level budget category
    is_discretionary: bool = field(default=True)                 # Can be cut from budget
    
    def to_dict(self):
        """Convert transaction to dictionary."""
        return {
            'transaction_date': self.transaction_date.strftime('%Y-%m-%d'),
            'post_date': self.post_date.strftime('%Y-%m-%d'),
            'description': self.description,
            'amount': self.amount,
            'category': self.category,
            'bank': self.bank,
            'type': self.type,
            'memo': self.memo,
            # Enhanced classification
            'expense_type': self.expense_type,
            'necessity': self.necessity,
            'recurrence': self.recurrence,
            'budget_category': self.budget_category,
            'is_discretionary': self.is_discretionary
        }
    
    def to_sheet_row(self):
        """Convert transaction to Google Sheets row format with enhanced columns."""
        return [
            self.transaction_date.strftime('%Y-%m-%d'),
            self.post_date.strftime('%Y-%m-%d'),
            self.description,
            self.amount,
            self.category,
            self.bank,
            self.type or '',
            self.memo or '',
            # Enhanced classification columns
            self.expense_type,
            self.necessity,
            self.recurrence,
            self.budget_category,
            'Yes' if self.is_discretionary else 'No'
        ]
    
    @property
    def month_year(self):
        """Get month-year string for grouping."""
        return self.transaction_date.strftime('%Y-%m')
    
    @property
    def is_expense(self):
        """Check if transaction is an expense (negative amount)."""
        return self.amount < 0
    
    @property
    def is_income(self):
        """Check if transaction is income (positive amount)."""
        return self.amount > 0
    
    @property
    def is_essential(self):
        """Check if this is an essential/needs expense."""
        return self.necessity == NecessityLevel.NEEDS
    
    @property
    def is_subscription(self):
        """Check if this is a subscription expense."""
        return self.recurrence == RecurrenceType.SUBSCRIPTION
    
    @property
    def is_fixed_expense(self):
        """Check if this is a fixed expense."""
        return self.expense_type == ExpenseType.FIXED
    
    @property
    def can_be_reduced(self):
        """Check if this expense can potentially be reduced."""
        return self.is_discretionary and self.is_expense
