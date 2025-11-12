from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    transaction_date: datetime
    description: str
    amount: float
    category: str
    bank: str
    
    @property
    def is_expense(self):
        return self.amount < 0
