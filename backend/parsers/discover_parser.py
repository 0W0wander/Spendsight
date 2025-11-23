import pandas as pd
from datetime import datetime
from backend.models.transaction import Transaction, RecurrenceType

class DiscoverParser:
    @staticmethod
    def parse(filepath, use_csv_categories=True):
        df = pd.read_csv(filepath)
        transactions = []
        
        for _, row in df.iterrows():
            try:
                cat = str(row.get('Category', 'Other')) if use_csv_categories else 'Other'
                amount = -float(row['Amount'])
                
                t = Transaction(
                    transaction_date=datetime.strptime(row['Trans. Date'], '%m/%d/%Y'),
                    post_date=datetime.strptime(row['Post Date'], '%m/%d/%Y'),
                    description=str(row['Description']).strip(),
                    amount=amount,
                    category=cat,
                    bank='Discover',
                    recurrence=RecurrenceType.ONE_TIME
                )
                transactions.append(t)
            except:
                continue
        
        return transactions
