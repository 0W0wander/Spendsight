"""Transaction data model."""
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


class NecessityLevel:
    """Essential vs Discretionary classification (50/30/20 rule)."""
    NEEDS = "Needs"              # 50% - Essential expenses
    FLEXIBLE_NEED = "Flexible Need"  # Expenses that are needed but have flexibility in amount
    WANTS = "Wants"              # 30% - Discretionary spending
    SAVINGS = "Savings"          # 20% - Financial goals
    UNKNOWN = "Unknown"
    # Note: Income is a CATEGORY, not a necessity level


class RecurrenceType:
    """Subscription and recurring payment classification."""
    SUBSCRIPTION = "Subscription"      # Recurring digital/service subscriptions
    RECURRING = "Recurring"            # Regular but non-subscription (rent, utilities)
    ONE_TIME = "One-time"              # Single purchases
    UNKNOWN = "Unknown"
    # Note: Income transactions can still be Recurring (e.g., paychecks)


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
    necessity: str = field(default=NecessityLevel.UNKNOWN)       # Needs/Wants/Savings
    recurrence: str = field(default=RecurrenceType.UNKNOWN)      # Subscription/Recurring/One-time
    note: Optional[str] = None                                   # User-added note for the transaction
    
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
            'necessity': self.necessity,
            'recurrence': self.recurrence,
            'note': self.note
        }
    
    def to_sheet_row(self):
        """Convert transaction to Google Sheets row format."""
        return [
            self.transaction_date.strftime('%Y-%m-%d'),
            self.post_date.strftime('%Y-%m-%d'),
            self.description,
            self.amount,
            self.category,
            self.bank,
            # Enhanced classification columns
            self.necessity,
            self.recurrence,
            self.note or ''
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
