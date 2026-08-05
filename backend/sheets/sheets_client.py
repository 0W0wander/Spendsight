"""Google Sheets API client."""
import gspread
import logging
import sys
import ssl
import certifi
import os
from google.oauth2.service_account import Credentials
from typing import List
from backend.models.transaction import Transaction
from backend.config import Config, BASE_DIR

# Set up logger
logger = logging.getLogger('spendsight')

# Fix SSL certificate issues on Windows with PyInstaller
# This ensures the certificate bundle is found correctly
if getattr(sys, 'frozen', False):
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

def _log_and_flush(message, level='info'):
    """Log a message and flush to ensure it's written before any crash."""
    if level == 'error':
        logger.error(message)
    else:
        logger.info(message)
    # Flush all handlers to ensure the message is written
    for handler in logger.handlers:
        handler.flush()

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
        self.last_error = None
        _log_and_flush(f"SheetsClient: Connecting... creds_path={Config.GOOGLE_CREDENTIALS_PATH}, sheet_id={Config.GOOGLE_SHEETS_ID[:20] if Config.GOOGLE_SHEETS_ID else 'None'}...")
        
        # Check if credentials file exists
        if not Config.GOOGLE_CREDENTIALS_PATH.exists():
            self.last_error = f"Credentials file not found at: {Config.GOOGLE_CREDENTIALS_PATH}"
            _log_and_flush(f"SheetsClient Error: {self.last_error}", 'error')
            return
        
        try:
            _log_and_flush("SheetsClient: Loading credentials...")
            credentials = Credentials.from_service_account_file(
                str(Config.GOOGLE_CREDENTIALS_PATH),
                scopes=self.SCOPES
            )
            _log_and_flush("SheetsClient: Authorizing with gspread...")
            self.client = gspread.authorize(credentials)
            
            if Config.GOOGLE_SHEETS_ID:
                try:
                    _log_and_flush("SheetsClient: Opening spreadsheet by key...")
                    # Add a small delay to ensure network stack is ready
                    import time
                    time.sleep(0.5)
                    _log_and_flush("SheetsClient: Making API call to Google...")
                    self.spreadsheet = self.client.open_by_key(Config.GOOGLE_SHEETS_ID)
                    _log_and_flush("SheetsClient: Connected successfully!")
                except gspread.exceptions.APIError as api_error:
                    error_details = str(api_error)
                    if "404" in error_details:
                        self.last_error = f"Sheet not found. Check if the Sheet ID is correct: {Config.GOOGLE_SHEETS_ID}"
                    elif "403" in error_details or "permission" in error_details.lower():
                        self.last_error = f"Permission denied. Share the sheet with: {credentials.service_account_email}"
                    else:
                        self.last_error = f"API Error: {error_details}"
                    print(f"Error connecting to Google Sheets: {self.last_error}")
                    self.client = None
            else:
                self.last_error = "No Google Sheets ID configured"
                print(f"Warning: {self.last_error}")
        except FileNotFoundError:
            self.last_error = f"Credentials file not found at: {Config.GOOGLE_CREDENTIALS_PATH}"
            _log_and_flush(f"SheetsClient Error: {self.last_error}", 'error')
            self.client = None
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {str(e)}" if str(e) else f"{type(e).__name__} (no details)"
            _log_and_flush(f"SheetsClient Error: {self.last_error}", 'error')
            import traceback
            _log_and_flush(traceback.format_exc(), 'error')
            self.client = None
        except BaseException as e:
            # Catch even system-level exceptions
            _log_and_flush(f"SheetsClient CRITICAL: {type(e).__name__}: {str(e)}", 'error')
            import traceback
            _log_and_flush(traceback.format_exc(), 'error')
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.client is not None and self.spreadsheet is not None
    
    def _get_or_create_worksheet(self, title: str, headers: List[str]):
        """Get existing worksheet or create new one. Ensures headers are present."""
        try:
            worksheet = self.spreadsheet.worksheet(title)
            # Check if headers exist, add them if sheet is empty
            first_row = worksheet.row_values(1)
            if not first_row or first_row[0] != headers[0]:
                # Sheet exists but is empty or has wrong headers - clear and add headers
                worksheet.clear()
                worksheet.append_row(headers)
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
                # Enhanced classification columns
                'Necessity',         # Needs/Wants/Savings
                'Recurrence',        # Subscription/Recurring/One-time
                'Note'               # User notes
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
                # Incremental sync - avoid duplicates based on key fields only
                # (date, description, amount, bank) - NOT category or other fields
                existing_data = all_transactions_sheet.get_all_values()
                
                # Create a set of existing transaction keys (date, description, amount, bank)
                # Column indices: 0=Transaction Date, 2=Description, 3=Amount, 5=Bank
                existing_keys = set()
                for row in existing_data[1:]:  # Skip header
                    if len(row) >= 6:
                        # Normalize amount for comparison (remove formatting)
                        try:
                            amount = str(float(row[3]))
                        except (ValueError, IndexError):
                            amount = row[3] if len(row) > 3 else ''
                        key = (row[0], row[2], amount, row[5])  # date, description, amount, bank
                        existing_keys.add(key)
                
                # Prepare new rows, checking against key fields only
                new_rows = []
                duplicate_count = 0
                for transaction in transactions:
                    row = [str(val) for val in transaction.to_sheet_row()]
                    # Create key from this transaction
                    key = (row[0], row[2], str(float(row[3])), row[5])
                    if key not in existing_keys:
                        new_rows.append(row)
                        existing_keys.add(key)  # Prevent duplicates within the batch
                    else:
                        duplicate_count += 1
                
                # Append new rows
                if new_rows:
                    all_transactions_sheet.append_rows(new_rows)
                synced_count = len(new_rows)
            
            # Sync by bank (case-insensitive; parsers store title-case bank names)
            chase_transactions = [t for t in transactions if t.bank.lower() == 'chase']
            discover_transactions = [t for t in transactions if t.bank.lower() == 'discover']
            td_transactions = [t for t in transactions if t.bank.lower() == 'td']
            
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

            if td_transactions:
                td_sheet = self._get_or_create_worksheet('TD', headers)
                if clear_first:
                    td_sheet.clear()
                    td_sheet.append_row(headers)
                td_rows = [[str(val) for val in t.to_sheet_row()] for t in td_transactions]
                if td_rows:
                    td_sheet.append_rows(td_rows)
            
            return {
                'success': True,
                'synced_count': synced_count,
                'total_count': len(transactions),
                'duplicate_count': len(transactions) - synced_count if not clear_first else 0
            }
            
        except Exception as e:
            return {'error': f'Error syncing to Google Sheets: {str(e)}'}
    
    def load_transactions(self, start_date=None) -> dict:
        """
        Load transactions from Google Sheets with optional date filtering.
        
        Args:
            start_date: Optional date object. If provided, only load transactions 
                       on or after this date.
        
        Returns:
            Dictionary with loaded transactions or error
        """
        _log_and_flush(f"SheetsClient: load_transactions called, start_date={start_date}")
        
        if not self.is_connected():
            _log_and_flush("SheetsClient: Not connected!", 'error')
            return {'error': 'Not connected to Google Sheets', 'transactions': []}
        
        try:
            # Try to get the "All Transactions" worksheet
            _log_and_flush("SheetsClient: Getting worksheet 'All Transactions'...")
            try:
                worksheet = self.spreadsheet.worksheet('All Transactions')
            except gspread.exceptions.WorksheetNotFound:
                _log_and_flush("SheetsClient: Worksheet not found, returning empty")
                return {'transactions': [], 'message': 'No transactions found in Google Sheets'}
            
            # Get all data
            _log_and_flush("SheetsClient: Fetching all values from worksheet...")
            all_data = worksheet.get_all_values()
            _log_and_flush(f"SheetsClient: Got {len(all_data)} rows from worksheet")
            
            if len(all_data) <= 1:  # Only header or empty
                return {'transactions': [], 'message': 'No transactions found in Google Sheets'}
            
            # Parse rows (skip header)
            transactions = []
            errors = []
            skipped_by_date = 0
            
            for row_num, row in enumerate(all_data[1:], start=2):
                try:
                    # Expected columns: Transaction Date, Post Date, Description, Amount, Category, 
                    # Bank, Necessity, Recurrence, Note
                    if len(row) < 6:  # Need at least the basic columns
                        continue
                    
                    from datetime import datetime
                    from backend.models.transaction import NecessityLevel, RecurrenceType
                    
                    # Parse dates
                    transaction_date = datetime.strptime(row[0], '%Y-%m-%d')
                    
                    # Filter by start_date if provided
                    if start_date is not None:
                        if transaction_date.date() < start_date:
                            skipped_by_date += 1
                            continue
                    
                    post_date = datetime.strptime(row[1], '%Y-%m-%d') if row[1] else transaction_date
                    
                    # Parse amount
                    amount = float(row[3]) if row[3] else 0.0
                    
                    # Create transaction object
                    transaction = Transaction(
                        transaction_date=transaction_date,
                        post_date=post_date,
                        description=row[2],
                        amount=amount,
                        category=row[4] if len(row) > 4 and row[4] else 'Other',
                        bank=row[5] if len(row) > 5 and row[5] else 'unknown',
                        # Enhanced classification columns
                        necessity=row[6] if len(row) > 6 and row[6] else NecessityLevel.UNKNOWN,
                        recurrence=row[7] if len(row) > 7 and row[7] else RecurrenceType.UNKNOWN,
                        note=row[8] if len(row) > 8 and row[8] else None
                    )
                    transactions.append(transaction)
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue
            
            _log_and_flush(f"SheetsClient: Successfully loaded {len(transactions)} transactions")
            
            return {
                'transactions': transactions,
                'loaded_count': len(transactions),
                'error_count': len(errors),
                'skipped_by_date': skipped_by_date,
                'errors': errors[:5] if errors else []  # Return first 5 errors for debugging
            }
            
        except Exception as e:
            import traceback
            _log_and_flush(f"SheetsClient: Exception in load_transactions: {str(e)}", 'error')
            _log_and_flush(traceback.format_exc(), 'error')
            return {'error': f'Error loading from Google Sheets: {str(e)}', 'transactions': []}
    
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
    
    def sync_period_notes(self, notes: dict) -> dict:
        """
        Sync period notes (weekly/monthly analysis) to Google Sheets.
        
        Args:
            notes: Dictionary mapping period_key to content
                   e.g., {'weekly_2024-01-07': 'My analysis...', 'monthly_2024-01': '...'}
            
        Returns:
            Dictionary with sync results
        """
        if not self.is_connected():
            return {'error': 'Not connected to Google Sheets'}
        
        try:
            headers = ['Period', 'Type', 'Date Range', 'Analysis Notes']
            
            # Get or create the Period Notes worksheet
            notes_sheet = self._get_or_create_worksheet('Period Notes', headers)
            
            # Clear and rebuild
            notes_sheet.clear()
            notes_sheet.append_row(headers)
            
            rows = []
            for period_key, content in sorted(notes.items(), reverse=True):
                if not content or not content.strip():
                    continue  # Skip empty notes
                
                # Parse period key to get type and date info
                if period_key.startswith('weekly_'):
                    period_type = 'Weekly'
                    date_str = period_key.replace('weekly_', '')
                    # Format: weekly_2024-01-07 (Sunday of that week)
                    try:
                        from datetime import datetime, timedelta
                        sunday = datetime.strptime(date_str, '%Y-%m-%d')
                        saturday = sunday + timedelta(days=6)
                        date_range = f"{sunday.strftime('%b %d')} - {saturday.strftime('%b %d, %Y')}"
                    except:
                        date_range = date_str
                elif period_key.startswith('monthly_'):
                    period_type = 'Monthly'
                    date_str = period_key.replace('monthly_', '')
                    # Format: monthly_2024-01
                    try:
                        from datetime import datetime
                        month_date = datetime.strptime(date_str + '-01', '%Y-%m-%d')
                        date_range = month_date.strftime('%B %Y')
                    except:
                        date_range = date_str
                else:
                    period_type = 'Other'
                    date_range = period_key
                
                rows.append([
                    period_key,
                    period_type,
                    date_range,
                    content
                ])
            
            if rows:
                notes_sheet.append_rows(rows)
            
            return {
                'success': True,
                'synced_count': len(rows),
                'total_notes': len(notes)
            }
            
        except Exception as e:
            return {'error': f'Error syncing period notes: {str(e)}'}
    
    @staticmethod
    def _keywords_to_cell(keywords) -> str:
        """Serialize keyword list to a sheet cell (AND keywords joined by ' | ')."""
        if not keywords:
            return ''
        if isinstance(keywords, str):
            return keywords
        return ' | '.join(str(k).strip() for k in keywords if str(k).strip())
    
    @staticmethod
    def _keywords_from_cell(cell: str) -> list:
        """Parse a keywords cell back into a list."""
        if not cell or not str(cell).strip():
            return []
        text = str(cell).strip()
        # Prefer explicit AND separator; fall back to comma for hand-edited rows
        if ' | ' in text:
            parts = text.split(' | ')
        elif '|' in text and 'OR' not in text.upper():
            parts = text.split('|')
        else:
            parts = [p.strip() for p in text.split(',')]
        return [p.strip() for p in parts if p.strip()]
    
    def sync_auto_tag_rules(self, rules: list) -> dict:
        """
        Sync auto-tag (category) rules to a dedicated Google Sheets tab.
        
        Args:
            rules: List of rule dicts (from CategoryRule.to_dict())
        """
        if not self.is_connected():
            return {'error': 'Not connected to Google Sheets'}
        
        try:
            import json
            headers = ['Id', 'Keywords', 'Priority', 'Enabled', 'Field', 'Category', 'Tags']
            sheet = self._get_or_create_worksheet('Auto-Tag Rules', headers)
            sheet.clear()
            sheet.append_row(headers)
            
            rows = []
            for rule in rules or []:
                tags = rule.get('tags') or {}
                if isinstance(tags, dict):
                    tags_str = json.dumps(tags, ensure_ascii=False)
                else:
                    tags_str = str(tags or '')
                rows.append([
                    rule.get('id', ''),
                    self._keywords_to_cell(rule.get('keywords', [])),
                    str(rule.get('priority', 0)),
                    'TRUE' if rule.get('enabled', True) else 'FALSE',
                    rule.get('field', 'category') or 'category',
                    rule.get('category', '') or '',
                    tags_str
                ])
            
            if rows:
                sheet.append_rows(rows)
            
            return {'success': True, 'synced_count': len(rows)}
        except Exception as e:
            return {'error': f'Error syncing auto-tag rules: {str(e)}'}
    
    def load_auto_tag_rules(self) -> dict:
        """Load auto-tag rules from the Auto-Tag Rules worksheet."""
        if not self.is_connected():
            return {'error': 'Not connected to Google Sheets', 'rules': []}
        
        try:
            import json
            try:
                sheet = self.spreadsheet.worksheet('Auto-Tag Rules')
            except gspread.exceptions.WorksheetNotFound:
                return {'success': True, 'rules': [], 'missing_sheet': True}
            
            values = sheet.get_all_values()
            if not values or len(values) < 2:
                return {'success': True, 'rules': []}
            
            # Map header names → index for resilience to column order
            headers = [h.strip().lower() for h in values[0]]
            def col(name, default=None):
                try:
                    return headers.index(name.lower())
                except ValueError:
                    return default
            
            idx_id = col('id', 0)
            idx_kw = col('keywords', 1)
            idx_pri = col('priority', 2)
            idx_en = col('enabled', 3)
            idx_field = col('field', 4)
            idx_cat = col('category', 5)
            idx_tags = col('tags', 6)
            
            rules = []
            for row in values[1:]:
                if not row or all(not str(c).strip() for c in row):
                    continue
                def cell(i):
                    return row[i].strip() if i is not None and i < len(row) else ''
                
                keywords = self._keywords_from_cell(cell(idx_kw))
                if not keywords:
                    continue
                
                tags_raw = cell(idx_tags)
                tags = {}
                if tags_raw:
                    try:
                        parsed = json.loads(tags_raw)
                        if isinstance(parsed, dict):
                            tags = {str(k): str(v) for k, v in parsed.items() if v}
                    except Exception:
                        tags = {}
                
                category = cell(idx_cat)
                field = cell(idx_field) or 'category'
                if not tags and category:
                    tags = {field: category}
                if tags and not category:
                    category = list(tags.values())[0]
                    field = list(tags.keys())[0]
                
                enabled_raw = cell(idx_en).upper()
                enabled = enabled_raw not in ('FALSE', '0', 'NO', 'OFF')
                
                try:
                    priority = int(float(cell(idx_pri) or '0'))
                except ValueError:
                    priority = 0
                
                rules.append({
                    'id': cell(idx_id) or None,
                    'keywords': keywords,
                    'priority': priority,
                    'enabled': enabled,
                    'field': field,
                    'category': category,
                    'tags': tags
                })
            
            return {'success': True, 'rules': rules}
        except Exception as e:
            return {'error': f'Error loading auto-tag rules: {str(e)}', 'rules': []}
    
    def sync_sweep_rules(self, rules: list) -> dict:
        """
        Sync sweep (broom/exclusion) rules to a dedicated Google Sheets tab.
        
        Args:
            rules: List of rule dicts (from ExclusionRule.to_dict())
        """
        if not self.is_connected():
            return {'error': 'Not connected to Google Sheets'}
        
        try:
            headers = ['Id', 'Title', 'Keywords', 'Enabled', 'Swept Count']
            sheet = self._get_or_create_worksheet('Sweep Rules', headers)
            sheet.clear()
            sheet.append_row(headers)
            
            rows = []
            for rule in rules or []:
                rows.append([
                    rule.get('id', ''),
                    rule.get('title', '') or '',
                    self._keywords_to_cell(rule.get('keywords', [])),
                    'TRUE' if rule.get('enabled', True) else 'FALSE',
                    str(rule.get('swept_count', 0))
                ])
            
            if rows:
                sheet.append_rows(rows)
            
            return {'success': True, 'synced_count': len(rows)}
        except Exception as e:
            return {'error': f'Error syncing sweep rules: {str(e)}'}
    
    def load_sweep_rules(self) -> dict:
        """Load sweep rules from the Sweep Rules worksheet."""
        if not self.is_connected():
            return {'error': 'Not connected to Google Sheets', 'rules': []}
        
        try:
            try:
                sheet = self.spreadsheet.worksheet('Sweep Rules')
            except gspread.exceptions.WorksheetNotFound:
                return {'success': True, 'rules': [], 'missing_sheet': True}
            
            values = sheet.get_all_values()
            if not values or len(values) < 2:
                return {'success': True, 'rules': []}
            
            headers = [h.strip().lower() for h in values[0]]
            def col(name, default=None):
                try:
                    return headers.index(name.lower())
                except ValueError:
                    return default
            
            idx_id = col('id', 0)
            idx_title = col('title', 1)
            idx_kw = col('keywords', 2)
            idx_en = col('enabled', 3)
            idx_swept = col('swept count', 4)
            
            rules = []
            for row in values[1:]:
                if not row or all(not str(c).strip() for c in row):
                    continue
                def cell(i):
                    return row[i].strip() if i is not None and i < len(row) else ''
                
                keywords = self._keywords_from_cell(cell(idx_kw))
                if not keywords:
                    continue
                
                enabled_raw = cell(idx_en).upper()
                enabled = enabled_raw not in ('FALSE', '0', 'NO', 'OFF')
                
                try:
                    swept_count = int(float(cell(idx_swept) or '0'))
                except ValueError:
                    swept_count = 0
                
                rules.append({
                    'id': cell(idx_id) or None,
                    'title': cell(idx_title),
                    'keywords': keywords,
                    'enabled': enabled,
                    'swept_count': swept_count
                })
            
            return {'success': True, 'rules': rules}
        except Exception as e:
            return {'error': f'Error loading sweep rules: {str(e)}', 'rules': []}

