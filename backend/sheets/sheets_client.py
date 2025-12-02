"""Google Sheets API client."""
import gspread
from google.oauth2.service_account import Credentials
from typing import List
from backend.models.transaction import Transaction
from backend.config import Config

class SheetsClient:
    """Client for interacting with Google Sheets."""
    
    # Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self):
        """Initialize the Google Sheets client."""
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets API."""
        try:
            credentials = Credentials.from_service_account_file(
                str(Config.GOOGLE_CREDENTIALS_PATH),
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)
            
            if Config.GOOGLE_SHEETS_ID:
                self.spreadsheet = self.client.open_by_key(Config.GOOGLE_SHEETS_ID)
            else:
                print("Warning: No Google Sheets ID configured")
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.client is not None and self.spreadsheet is not None
    
    def _get_or_create_worksheet(self, title: str, headers: List[str]):
        """Get existing worksheet or create new one."""
        try:
            worksheet = self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))
            worksheet.append_row(headers)
        
        return worksheet
    
    def sync_transactions(self, transactions: List[Transaction], clear_first: bool = False) -> dict:
        """
        Sync transactions to Google Sheets.
        
        Args:
            transactions: List of Transaction objects
            clear_first: If True, clear sheets before syncing (full re-sync)
            
        Returns:
            Dictionary with sync results
        """
        if not self.is_connected():
            return {'error': 'Not connected to Google Sheets'}
        
        try:
            headers = [
                'Transaction Date',
                'Post Date',
                'Description',
                'Amount',
                'Category',
                'Bank',
                'Type',
                'Memo',
                # Enhanced classification columns
                'Expense Type',      # Fixed/Variable (recurring only)
                'Necessity',         # Needs/Wants/Savings
                'Recurrence',        # Subscription/Recurring/One-time
                'Budget Category',   # High-level budget category
                'Discretionary'      # Yes/No
            ]
            
            # Sync to "All Transactions" sheet
            all_transactions_sheet = self._get_or_create_worksheet('All Transactions', headers)
            
            if clear_first:
                # Clear and re-sync all data
                all_transactions_sheet.clear()
                all_transactions_sheet.append_row(headers)
                new_rows = [[str(val) for val in t.to_sheet_row()] for t in transactions]
                if new_rows:
                    all_transactions_sheet.append_rows(new_rows)
                synced_count = len(new_rows)
            else:
                # Incremental sync - avoid duplicates
                existing_data = all_transactions_sheet.get_all_values()
                existing_rows = set(tuple(row) for row in existing_data[1:])  # Skip header
                
                # Prepare new rows
                new_rows = []
                for transaction in transactions:
                    row = [str(val) for val in transaction.to_sheet_row()]
                    if tuple(row) not in existing_rows:
                        new_rows.append(row)
                
                # Append new rows
                if new_rows:
                    all_transactions_sheet.append_rows(new_rows)
                synced_count = len(new_rows)
            
            # Sync by bank
            chase_transactions = [t for t in transactions if t.bank == 'chase']
            discover_transactions = [t for t in transactions if t.bank == 'discover']
            
            if chase_transactions:
                chase_sheet = self._get_or_create_worksheet('Chase', headers)
                if clear_first:
                    chase_sheet.clear()
                    chase_sheet.append_row(headers)
                chase_rows = [[str(val) for val in t.to_sheet_row()] for t in chase_transactions]
                if chase_rows:
                    chase_sheet.append_rows(chase_rows)
            
            if discover_transactions:
                discover_sheet = self._get_or_create_worksheet('Discover', headers)
                if clear_first:
                    discover_sheet.clear()
                    discover_sheet.append_row(headers)
                discover_rows = [[str(val) for val in t.to_sheet_row()] for t in discover_transactions]
                if discover_rows:
                    discover_sheet.append_rows(discover_rows)
            
            return {
                'success': True,
                'synced_count': synced_count,
                'total_count': len(transactions),
                'duplicate_count': len(transactions) - synced_count if not clear_first else 0
            }
            
        except Exception as e:
            return {'error': f'Error syncing to Google Sheets: {str(e)}'}
    
    def create_monthly_summary(self, transactions: List[Transaction]) -> dict:
        """
        Create monthly summary worksheet.
        
        Args:
            transactions: List of Transaction objects
            
        Returns:
            Dictionary with results
        """
        if not self.is_connected():
            return {'error': 'Not connected to Google Sheets'}
        
        try:
            # Group by month
            from collections import defaultdict
            monthly_data = defaultdict(lambda: {'spent': 0, 'income': 0, 'count': 0})
            
            for t in transactions:
                month_key = t.month_year
                if t.is_expense:
                    monthly_data[month_key]['spent'] += abs(t.amount)
                else:
                    monthly_data[month_key]['income'] += t.amount
                monthly_data[month_key]['count'] += 1
            
            # Prepare summary data
            headers = ['Month', 'Transactions', 'Income', 'Spent', 'Net', 'Savings Rate']
            rows = []
            
            for month in sorted(monthly_data.keys(), reverse=True):
                data = monthly_data[month]
                income = round(data['income'], 2)
                spent = round(data['spent'], 2)
                net = round(income - spent, 2)
                savings_rate = f"{(net / income * 100):.1f}%" if income > 0 else "N/A"
                
                rows.append([
                    month,
                    data['count'],
                    income,
                    spent,
                    net,
                    savings_rate
                ])
            
            # Create/update worksheet
            summary_sheet = self._get_or_create_worksheet('Monthly Summary', headers)
            summary_sheet.clear()
            summary_sheet.append_row(headers)
            summary_sheet.append_rows(rows)
            
            return {'success': True, 'months': len(rows)}
            
        except Exception as e:
            return {'error': f'Error creating monthly summary: {str(e)}'}

