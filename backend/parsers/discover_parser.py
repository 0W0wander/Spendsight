import pandas as pd
from datetime import datetime
from backend.models.transaction import Transaction

class DiscoverParser:
    @staticmethod
    def parse(filepath):
        df = pd.read_csv(filepath)
        transactions = []
        
        for _, row in df.iterrows():
            try:
                # Discover uses positive for expenses
                amount = -float(row['Amount'])
                
                t = Transaction(
                    transaction_date=datetime.strptime(row['Trans. Date'], '%m/%d/%Y'),
                    description=str(row['Description']).strip(),
                    amount=amount,
                    category=str(row.get('Category', 'Other')),
                    bank='Discover'
                )
                transactions.append(t)
            except:
                continue
        
        return transactions
