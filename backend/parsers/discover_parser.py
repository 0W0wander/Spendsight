"""Discover CSV parser."""
import pandas as pd
from datetime import datetime
from typing import List
from backend.models.transaction import Transaction, RecurrenceType
from backend.analytics.expense_classifier import ExpenseClassifier

class DiscoverParser:
    """Parser for Discover card CSV files."""
    
    # Expected column names from Discover CSV
    EXPECTED_COLUMNS = {
        'Trans. Date',
        'Post Date',
        'Description',
        'Amount',
        'Category'
    }
    
    # Normalize Discover categories to standard categories
    CATEGORY_MAP = {
        'travel/ entertainment': 'Entertainment',
        'travel/entertainment': 'Entertainment',
        'merchandise': 'Shopping',
        'restaurants': 'Food & Dining',
        'supermarkets': 'Groceries',
        'gasoline': 'Gas & Fuel',
        'services': 'Services',
        'payments and credits': 'Payment',
        'awards and rebate credits': 'Rewards',
        'government services': 'Government',
        'education': 'Education',
        'medical services': 'Healthcare',
        'department stores': 'Shopping',
        'automotive': 'Auto & Transport',
        'home improvement': 'Home',
        'warehouse clubs': 'Shopping',
        'utilities': 'Bills & Utilities',
        'internet': 'Bills & Utilities',
        'cable/satellite': 'Bills & Utilities',
    }
    
    @staticmethod
    def parse(file_path: str, use_csv_categories: bool = False) -> List[Transaction]:
        """
        Parse Discover CSV file and return list of transactions.
        
        Args:
            file_path: Path to the Discover CSV file
            use_csv_categories: If True, use categories from CSV and skip auto-classification.
                               If False, apply auto-tagging rules.
            
        Returns:
            List of Transaction objects with full classification
        """
        try:
            # Read CSV file (index_col=False prevents pandas from using first column as index)
            df = pd.read_csv(file_path, index_col=False)
            
            # Validate columns
            if not DiscoverParser._validate_columns(df):
                # Try flexible parsing
                transactions = DiscoverParser._parse_flexible(df, use_csv_categories)
                return transactions
            
            transactions = []
            
            for _, row in df.iterrows():
                try:
                    # Parse dates
                    trans_date = datetime.strptime(str(row['Trans. Date']).strip(), '%m/%d/%Y')
                    post_date = datetime.strptime(str(row['Post Date']).strip(), '%m/%d/%Y')
                    
                    # Parse amount - Discover uses positive for charges, negative for credits
                    # We flip the sign to match budgeting convention: negative = expense, positive = income
                    amount_str = str(row['Amount']).replace(',', '').replace('$', '').strip()
                    amount = -float(amount_str)  # Flip sign for credit cards
                    
                    # Get and normalize category - only if using CSV categories
                    raw_category = str(row['Category']).strip() if pd.notna(row['Category']) else 'Other'
                    if use_csv_categories:
                        category = DiscoverParser._normalize_category(raw_category)
                    else:
                        # Set to 'Other' so auto-tagging rules can apply
                        category = 'Other'
                    
                    # Get description
                    description = str(row['Description']).strip().strip('"')
                    
                    # Determine transaction type based on category and amount
                    trans_type = DiscoverParser._determine_type(raw_category, amount)
                    
                    transaction = Transaction(
                        transaction_date=trans_date,
                        post_date=post_date,
                        description=description,
                        amount=amount,
                        category=category,
                        bank='Discover',
                        type=trans_type,
                        memo=None,
                        recurrence=RecurrenceType.ONE_TIME  # Default to one-time
                    )
                    transactions.append(transaction)
                except Exception as e:
                    print(f"Error parsing Discover row: {e}")
                    continue
            
            # Only apply auto-classification if NOT using CSV categories
            if not use_csv_categories:
                return ExpenseClassifier.classify_batch(transactions)
            
            return transactions
            
        except Exception as e:
            raise Exception(f"Error parsing Discover CSV: {str(e)}")
    
    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> bool:
        """Validate that all required columns are present."""
        df_columns = set(df.columns)
        required_columns = DiscoverParser.EXPECTED_COLUMNS
        return required_columns.issubset(df_columns)
    
    @staticmethod
    def _parse_flexible(df: pd.DataFrame, use_csv_categories: bool = False) -> List[Transaction]:
        """Flexibly parse Discover CSV by finding common column names."""
        transactions = []
        columns = df.columns.tolist()
        
        # Map possible column names
        date_candidates = ['Trans. Date', 'Transaction Date', 'Date', 'Trans Date']
        post_candidates = ['Post Date', 'Posted Date', 'Posting Date']
        desc_candidates = ['Description', 'Merchant', 'Name', 'Payee']
        amount_candidates = ['Amount', 'Transaction Amount', 'Charge']
        category_candidates = ['Category', 'Type', 'Transaction Type']
        
        def find_column(candidates):
            for c in candidates:
                if c in columns:
                    return c
            return None
        
        date_col = find_column(date_candidates)
        post_col = find_column(post_candidates)
        desc_col = find_column(desc_candidates)
        amount_col = find_column(amount_candidates)
        category_col = find_column(category_candidates)
        
        if not all([date_col, desc_col, amount_col]):
            raise ValueError("Could not find required columns in Discover CSV")
        
        for _, row in df.iterrows():
            try:
                # Parse date
                date_str = str(row[date_col]).strip()
                try:
                    trans_date = datetime.strptime(date_str, '%m/%d/%Y')
                except:
                    trans_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Parse post date (use trans date if not available)
                if post_col and pd.notna(row[post_col]):
                    post_str = str(row[post_col]).strip()
                    try:
                        post_date = datetime.strptime(post_str, '%m/%d/%Y')
                    except:
                        post_date = datetime.strptime(post_str, '%Y-%m-%d')
                else:
                    post_date = trans_date
                
                # Parse amount - flip sign for credit card convention
                amount_str = str(row[amount_col]).replace(',', '').replace('$', '').strip()
                amount = -float(amount_str)  # Flip sign for credit cards
                
                # Get description
                description = str(row[desc_col]).strip()
                
                # Get category - only if using CSV categories
                if use_csv_categories:
                    raw_category = 'Other'
                    if category_col and pd.notna(row[category_col]):
                        raw_category = str(row[category_col]).strip()
                    category = DiscoverParser._normalize_category(raw_category)
                else:
                    # Set to 'Other' so auto-tagging rules can apply
                    category = 'Other'
                
                transaction = Transaction(
                    transaction_date=trans_date,
                    post_date=post_date,
                    description=description,
                    amount=amount,
                    category=category,
                    bank='Discover',
                    type=None,
                    memo=None,
                    recurrence=RecurrenceType.ONE_TIME  # Default to one-time
                )
                transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing Discover row: {e}")
                continue
        
        # Only apply auto-classification if NOT using CSV categories
        if not use_csv_categories:
            return ExpenseClassifier.classify_batch(transactions)
        
        return transactions
    
    @staticmethod
    def _normalize_category(raw_category: str) -> str:
        """Normalize Discover category to a standard category."""
        category_lower = raw_category.lower().strip()
        return DiscoverParser.CATEGORY_MAP.get(category_lower, raw_category)
    
    @staticmethod
    def _determine_type(category: str, amount: float) -> str:
        """Determine transaction type based on category and amount."""
        category_lower = category.lower()
        
        if 'payment' in category_lower:
            return 'Payment'
        elif 'credit' in category_lower or 'rebate' in category_lower:
            return 'Credit'
        elif amount > 0:
            return 'Refund'  # After sign flip, positive = was negative = refund/credit
        else:
            return 'Purchase'
    
    @staticmethod
    def get_summary(transactions: List[Transaction]) -> dict:
        """Get summary statistics for Discover transactions."""
        if not transactions:
            return {}
        
        total_spent = sum(abs(t.amount) for t in transactions if t.is_expense)
        total_income = sum(t.amount for t in transactions if t.is_income)
        
        return {
            'bank': 'Discover',
            'total_transactions': len(transactions),
            'total_spent': round(total_spent, 2),
            'total_income': round(total_income, 2),
            'net': round(total_income - total_spent, 2),
            'date_range': {
                'start': min(t.transaction_date for t in transactions).strftime('%Y-%m-%d'),
                'end': max(t.transaction_date for t in transactions).strftime('%Y-%m-%d')
            }
        }
