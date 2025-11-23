import pandas as pd
from datetime import datetime
from backend.models.transaction import Transaction, RecurrenceType

class ChaseParser:
    @staticmethod
    def parse(filepath, use_csv_categories=True):
        df = pd.read_csv(filepath)
        transactions = []
        
        if 'Transaction Date' in df.columns:
            for _, row in df.iterrows():
                try:
                    cat = str(row.get('Category', 'Other')) if use_csv_categories else 'Other'
                    t = Transaction(
                        transaction_date=datetime.strptime(row['Transaction Date'], '%m/%d/%Y'),
                        post_date=datetime.strptime(row['Post Date'], '%m/%d/%Y'),
                        description=str(row['Description']).strip(),
                        amount=float(row['Amount']),
                        category=cat,
                        bank='Chase',
                        type=str(row.get('Type', '')),
                        recurrence=RecurrenceType.ONE_TIME
                    )
                    transactions.append(t)
                except:
                    continue
        
        elif 'Posting Date' in df.columns:
            for _, row in df.iterrows():
                try:
                    date = datetime.strptime(str(row['Posting Date']).strip(), '%m/%d/%Y')
                    amt = float(str(row['Amount']).replace(',', ''))
                    t = Transaction(
                        transaction_date=date,
                        post_date=date,
                        description=str(row['Description']).strip(),
                        amount=amt,
                        category='Other',
                        bank='Chase',
                        recurrence=RecurrenceType.ONE_TIME
                    )
                    transactions.append(t)
                except:
                    continue
        
        return transactions
