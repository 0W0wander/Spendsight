import pandas as pd
from datetime import datetime
from backend.models.transaction import Transaction

class ChaseParser:
    @staticmethod
    def parse(filepath):
        df = pd.read_csv(filepath)
        transactions = []
        
        for _, row in df.iterrows():
            try:
                t = Transaction(
                    transaction_date=datetime.strptime(row['Transaction Date'], '%m/%d/%Y'),
                    description=row['Description'],
                    amount=float(row['Amount']),
                    category=row.get('Category', 'Other'),
                    bank='Chase'
                )
                transactions.append(t)
            except:
                pass
        
        return transactions
