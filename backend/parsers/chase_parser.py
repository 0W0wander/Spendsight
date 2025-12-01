"""Chase CSV parser."""
import pandas as pd
from datetime import datetime
from typing import List
from backend.models.transaction import Transaction
from backend.analytics.expense_classifier import ExpenseClassifier

class ChaseParser:
    """Parser for Chase bank CSV files."""
    
    # Chase checking/savings account format
    CHECKING_COLUMNS = {'Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance'}
    
    # Chase credit card format (if they use a different format)
    CREDIT_CARD_COLUMNS = {'Transaction Date', 'Post Date', 'Description', 'Category', 'Type', 'Amount'}
    
    # Category mapping based on Chase transaction types
    TYPE_CATEGORY_MAP = {
        'ACH_CREDIT': 'Income',
        'ACH_DEBIT': 'Bills & Utilities',
        'LOAN_PMT': 'Debt Payment',
        'PARTNERFI_TO_CHASE': 'Transfer',
        'QUICKPAY_CREDIT': 'Transfer',
        'QUICKPAY_DEBIT': 'Transfer',
        'DEBIT_CARD': 'Shopping',
        'ATMSURCHARGE': 'Fees',
        'ATM': 'Cash & ATM',
        'FEE_TRANSACTION': 'Fees',
        'CHECK_DEPOSIT': 'Income',
        'CHECK_PAID': 'Bills & Utilities',
        'MISC_CREDIT': 'Other Income',
        'MISC_DEBIT': 'Other',
    }
    
    @staticmethod
    def parse(file_path: str) -> List[Transaction]:
        """
        Parse Chase CSV file and return list of transactions.
        
        Args:
            file_path: Path to the Chase CSV file
            
        Returns:
            List of Transaction objects with full classification
        """
        try:
            # Read CSV file (index_col=False prevents pandas from using first column as index)
            df = pd.read_csv(file_path, index_col=False)
            
            # Determine which format this is
            df_columns = set(df.columns)
            
            if ChaseParser.CHECKING_COLUMNS.issubset(df_columns):
                transactions = ChaseParser._parse_checking_format(df)
            elif ChaseParser.CREDIT_CARD_COLUMNS.issubset(df_columns):
                transactions = ChaseParser._parse_credit_card_format(df)
            else:
                # Try to be flexible - look for key columns
                transactions = ChaseParser._parse_flexible(df)
            
            # Apply multi-dimensional classification
            return ExpenseClassifier.classify_batch(transactions)
            
        except Exception as e:
            raise Exception(f"Error parsing Chase CSV: {str(e)}")
    
    @staticmethod
    def _parse_checking_format(df: pd.DataFrame) -> List[Transaction]:
        """Parse Chase checking/savings account CSV format."""
        transactions = []
        
        for _, row in df.iterrows():
            try:
                # Parse date (Posting Date)
                post_date = datetime.strptime(str(row['Posting Date']).strip(), '%m/%d/%Y')
                
                # Parse amount - clean it up
                amount_str = str(row['Amount']).replace(',', '').replace('$', '').strip()
                amount = float(amount_str)
                
                # Get description
                description = str(row['Description']).strip().strip('"')
                
                # Determine category from Type
                chase_type = str(row['Type']).strip() if pd.notna(row['Type']) else ''
                category = ChaseParser.TYPE_CATEGORY_MAP.get(chase_type, 'Other')
                
                # Further categorize based on description keywords
                category = ChaseParser._categorize_by_description(description, category)
                
                # Details indicates CREDIT/DEBIT
                details = str(row['Details']).strip() if pd.notna(row['Details']) else ''
                
                transaction = Transaction(
                    transaction_date=post_date,  # Use posting date as transaction date
                    post_date=post_date,
                    description=description,
                    amount=amount,
                    category=category,
                    bank='chase',
                    type=chase_type if chase_type else details,
                    memo=None
                )
                transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing Chase row: {e}")
                continue
        
        return transactions
    
    @staticmethod
    def _parse_credit_card_format(df: pd.DataFrame) -> List[Transaction]:
        """Parse Chase credit card CSV format."""
        transactions = []
        
        for _, row in df.iterrows():
            try:
                transaction = Transaction(
                    transaction_date=datetime.strptime(row['Transaction Date'], '%m/%d/%Y'),
                    post_date=datetime.strptime(row['Post Date'], '%m/%d/%Y'),
                    description=str(row['Description']).strip(),
                    amount=float(row['Amount']),
                    category=str(row['Category']).strip() if pd.notna(row['Category']) else 'Uncategorized',
                    bank='chase',
                    type=str(row['Type']).strip() if pd.notna(row['Type']) else None,
                    memo=str(row.get('Memo', '')).strip() if 'Memo' in row and pd.notna(row.get('Memo')) else None
                )
                transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing Chase row: {e}")
                continue
        
        return transactions
    
    @staticmethod
    def _parse_flexible(df: pd.DataFrame) -> List[Transaction]:
        """Flexibly parse Chase CSV by finding common column names."""
        transactions = []
        columns = df.columns.tolist()
        
        # Try to find date column
        date_col = None
        for col in ['Posting Date', 'Transaction Date', 'Date', 'Post Date']:
            if col in columns:
                date_col = col
                break
        
        if not date_col:
            raise ValueError("Could not find a date column in Chase CSV")
        
        # Try to find amount column
        amount_col = None
        for col in ['Amount', 'Transaction Amount', 'Debit', 'Credit']:
            if col in columns:
                amount_col = col
                break
        
        if not amount_col:
            raise ValueError("Could not find an amount column in Chase CSV")
        
        # Try to find description column
        desc_col = None
        for col in ['Description', 'Merchant', 'Payee', 'Name']:
            if col in columns:
                desc_col = col
                break
        
        if not desc_col:
            raise ValueError("Could not find a description column in Chase CSV")
        
        for _, row in df.iterrows():
            try:
                # Parse date
                date_str = str(row[date_col]).strip()
                try:
                    parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                except:
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Parse amount
                amount_str = str(row[amount_col]).replace(',', '').replace('$', '').strip()
                amount = float(amount_str)
                
                # Get description
                description = str(row[desc_col]).strip()
                
                # Try to get category
                category = 'Uncategorized'
                if 'Category' in columns and pd.notna(row['Category']):
                    category = str(row['Category']).strip()
                elif 'Type' in columns and pd.notna(row['Type']):
                    chase_type = str(row['Type']).strip()
                    category = ChaseParser.TYPE_CATEGORY_MAP.get(chase_type, 'Other')
                
                transaction = Transaction(
                    transaction_date=parsed_date,
                    post_date=parsed_date,
                    description=description,
                    amount=amount,
                    category=category,
                    bank='chase',
                    type=None,
                    memo=None
                )
                transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing Chase row: {e}")
                continue
        
        return transactions
    
    @staticmethod
    def _categorize_by_description(description: str, default_category: str) -> str:
        """Categorize transaction based on description keywords."""
        desc_lower = description.lower()
        
        # Payment/Transfer keywords
        if any(kw in desc_lower for kw in ['zelle', 'venmo', 'paypal', 'transfer', 'payment to', 'payment from']):
            return 'Transfer'
        
        # Income keywords
        if any(kw in desc_lower for kw in ['direct dep', 'payroll', 'salary', 'deposit', 'dirdep']):
            return 'Income'
        
        # Bills
        if any(kw in desc_lower for kw in ['electric', 'gas bill', 'internet', 'phone', 'insurance', 'utility']):
            return 'Bills & Utilities'
        
        return default_category
    
    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> bool:
        """Validate that required columns are present (legacy method)."""
        df_columns = set(df.columns)
        return (ChaseParser.CHECKING_COLUMNS.issubset(df_columns) or 
                ChaseParser.CREDIT_CARD_COLUMNS.issubset(df_columns))
    
    @staticmethod
    def get_summary(transactions: List[Transaction]) -> dict:
        """Get summary statistics for Chase transactions."""
        if not transactions:
            return {}
        
        total_spent = sum(abs(t.amount) for t in transactions if t.is_expense)
        total_income = sum(t.amount for t in transactions if t.is_income)
        
        return {
            'bank': 'Chase',
            'total_transactions': len(transactions),
            'total_spent': round(total_spent, 2),
            'total_income': round(total_income, 2),
            'net': round(total_income - total_spent, 2),
            'date_range': {
                'start': min(t.transaction_date for t in transactions).strftime('%Y-%m-%d'),
                'end': max(t.transaction_date for t in transactions).strftime('%Y-%m-%d')
            }
        }
