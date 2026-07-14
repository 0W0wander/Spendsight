"""TD Bank CSV parser."""
import pandas as pd
from datetime import datetime
from typing import List, Optional
from backend.models.transaction import Transaction, RecurrenceType
from backend.analytics.expense_classifier import ExpenseClassifier


class TDParser:
    """Parser for TD Bank checking and credit card CSV files."""

    # TD Bank export format (same columns for checking and credit)
    EXPECTED_COLUMNS = {
        'Date',
        'Description',
        'Debit',
        'Credit',
    }

    CHARACTERISTIC_COLUMNS = {
        'Bank RTN',
        'Account Running Balance',
        'Transaction Type',
    }

    # Category mapping based on TD transaction types when using CSV categories
    TYPE_CATEGORY_MAP = {
        'DEBIT': 'Other',
        'CREDIT': 'Income',
        'XFER': 'Transfer',
        'DEP': 'Income',
        'CHECK': 'Bills & Utilities',
    }

    @staticmethod
    def parse(
        file_path: str,
        use_csv_categories: bool = False,
        account_type: str = 'checking',
    ) -> List[Transaction]:
        """
        Parse TD Bank CSV file and return list of transactions.

        Args:
            file_path: Path to the TD Bank CSV file
            use_csv_categories: If True, derive categories from transaction type /
                description. If False, set category to 'Other' for auto-tagging.
            account_type: 'checking' or 'credit' (informational; format is the same)

        Returns:
            List of Transaction objects with full classification
        """
        try:
            df = pd.read_csv(file_path, index_col=False)
            # Normalize column names (strip whitespace)
            df.columns = [str(c).strip() for c in df.columns]

            if not TDParser._validate_columns(df):
                transactions = TDParser._parse_flexible(df, use_csv_categories)
            else:
                transactions = TDParser._parse_standard(df, use_csv_categories)

            for t in transactions:
                t.recurrence = RecurrenceType.ONE_TIME

            if not use_csv_categories:
                return ExpenseClassifier.classify_batch(transactions)

            return transactions

        except Exception as e:
            raise Exception(f"Error parsing TD Bank CSV: {str(e)}")

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> bool:
        """Validate that required columns are present."""
        return TDParser.EXPECTED_COLUMNS.issubset(set(df.columns))

    @staticmethod
    def _parse_amount(row) -> Optional[float]:
        """
        Build a signed amount from Debit/Credit columns.

        Debit  -> negative (expense)
        Credit -> positive (income / payment received)
        """
        debit_val = row.get('Debit') if 'Debit' in row.index else None
        credit_val = row.get('Credit') if 'Credit' in row.index else None

        def _to_float(val) -> Optional[float]:
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            s = str(val).replace(',', '').replace('$', '').strip()
            if not s or s.lower() == 'nan':
                return None
            return float(s)

        debit = _to_float(debit_val)
        credit = _to_float(credit_val)

        if debit is not None and debit != 0:
            return -abs(debit)
        if credit is not None and credit != 0:
            return abs(credit)
        return None

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse TD date strings (YYYY-MM-DD or M/D/YYYY)."""
        date_str = str(date_str).strip()
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unrecognized date format: {date_str}")

    @staticmethod
    def _parse_standard(df: pd.DataFrame, use_csv_categories: bool = False) -> List[Transaction]:
        """Parse standard TD Bank Debit/Credit CSV format."""
        transactions = []

        for _, row in df.iterrows():
            try:
                parsed_date = TDParser._parse_date(row['Date'])
                amount = TDParser._parse_amount(row)
                if amount is None:
                    continue

                description = str(row['Description']).strip().strip('"')
                td_type = (
                    str(row['Transaction Type']).strip()
                    if 'Transaction Type' in row.index and pd.notna(row.get('Transaction Type'))
                    else ''
                )

                if use_csv_categories:
                    category = TDParser.TYPE_CATEGORY_MAP.get(td_type.upper(), 'Other')
                    category = TDParser._categorize_by_description(description, category)
                else:
                    category = 'Other'

                memo = None
                if 'Check Number' in row.index and pd.notna(row.get('Check Number')):
                    check_no = str(row['Check Number']).strip()
                    if check_no and check_no.lower() != 'nan':
                        memo = f"Check #{check_no}"

                transaction = Transaction(
                    transaction_date=parsed_date,
                    post_date=parsed_date,
                    description=description,
                    amount=amount,
                    category=category,
                    bank='TD',
                    type=td_type or None,
                    memo=memo,
                )
                transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing TD Bank row: {e}")
                continue

        return transactions

    @staticmethod
    def _parse_flexible(df: pd.DataFrame, use_csv_categories: bool = False) -> List[Transaction]:
        """Flexibly parse TD Bank CSV by finding common column names."""
        columns = df.columns.tolist()

        date_col = next((c for c in ['Date', 'Transaction Date', 'Posting Date'] if c in columns), None)
        desc_col = next((c for c in ['Description', 'Merchant', 'Payee', 'Name'] if c in columns), None)
        debit_col = next((c for c in ['Debit', 'Withdrawal'] if c in columns), None)
        credit_col = next((c for c in ['Credit', 'Deposit'] if c in columns), None)
        amount_col = next((c for c in ['Amount', 'Transaction Amount'] if c in columns), None)
        type_col = next((c for c in ['Transaction Type', 'Type'] if c in columns), None)

        if not date_col or not desc_col:
            raise ValueError("Could not find required columns in TD Bank CSV")
        if not debit_col and not credit_col and not amount_col:
            raise ValueError("Could not find amount columns in TD Bank CSV")

        transactions = []
        for _, row in df.iterrows():
            try:
                parsed_date = TDParser._parse_date(row[date_col])
                description = str(row[desc_col]).strip().strip('"')

                if debit_col or credit_col:
                    # Temporarily map to expected names for _parse_amount
                    amount_row = pd.Series({
                        'Debit': row[debit_col] if debit_col else None,
                        'Credit': row[credit_col] if credit_col else None,
                    })
                    amount = TDParser._parse_amount(amount_row)
                else:
                    amount_str = str(row[amount_col]).replace(',', '').replace('$', '').strip()
                    amount = float(amount_str)

                if amount is None:
                    continue

                td_type = (
                    str(row[type_col]).strip()
                    if type_col and pd.notna(row[type_col])
                    else ''
                )

                if use_csv_categories:
                    category = TDParser.TYPE_CATEGORY_MAP.get(td_type.upper(), 'Other')
                    category = TDParser._categorize_by_description(description, category)
                else:
                    category = 'Other'

                transaction = Transaction(
                    transaction_date=parsed_date,
                    post_date=parsed_date,
                    description=description,
                    amount=amount,
                    category=category,
                    bank='TD',
                    type=td_type or None,
                    memo=None,
                )
                transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing TD Bank row: {e}")
                continue

        return transactions

    @staticmethod
    def _categorize_by_description(description: str, default_category: str) -> str:
        """Refine category based on description keywords."""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in [
            'zelle', 'venmo', 'paypal', 'transfer', 'xfer', 'ext trnsfr', 'payment to', 'payment from'
        ]):
            return 'Transfer'

        if any(kw in desc_lower for kw in [
            'payroll', 'direct dep', 'salary', 'dirdep', 'deposit'
        ]):
            return 'Income'

        if any(kw in desc_lower for kw in [
            'atm', 'withdraw', 'dda withdraw'
        ]):
            return 'Cash & ATM'

        if any(kw in desc_lower for kw in [
            'electric', 'gas bill', 'internet', 'phone', 'insurance', 'utility', 'web pmts'
        ]):
            return 'Bills & Utilities'

        if any(kw in desc_lower for kw in [
            'wal mart', 'walmart', 'target', 'costco', 'grocery', 'supermarket'
        ]):
            return 'Groceries'

        if 'cash back' in desc_lower or 'rewards' in desc_lower:
            return 'Rewards'

        return default_category

    @staticmethod
    def get_summary(transactions: List[Transaction]) -> dict:
        """Get summary statistics for TD Bank transactions."""
        if not transactions:
            return {}

        total_spent = sum(abs(t.amount) for t in transactions if t.is_expense)
        total_income = sum(t.amount for t in transactions if t.is_income)

        return {
            'bank': 'TD',
            'total_transactions': len(transactions),
            'total_spent': round(total_spent, 2),
            'total_income': round(total_income, 2),
            'net': round(total_income - total_spent, 2),
            'date_range': {
                'start': min(t.transaction_date for t in transactions).strftime('%Y-%m-%d'),
                'end': max(t.transaction_date for t in transactions).strftime('%Y-%m-%d'),
            },
        }
