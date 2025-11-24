import gspread
from google.oauth2.service_account import Credentials
from backend.config import Config

class SheetsClient:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self):
        self.spreadsheet = None
        self.last_error = None
        self._connect()
    
    def _connect(self):
        try:
            if not Config.GOOGLE_CREDENTIALS_PATH.exists():
                self.last_error = "credentials.json not found"
                return
            
            creds = Credentials.from_service_account_file(
                str(Config.GOOGLE_CREDENTIALS_PATH),
                scopes=self.SCOPES
            )
            client = gspread.authorize(creds)
            self.spreadsheet = client.open_by_key(Config.GOOGLE_SHEETS_ID)
        except Exception as e:
            self.last_error = str(e)
    
    def is_connected(self):
        return self.spreadsheet is not None
    
    def sync_transactions(self, transactions, clear_first=False):
        if not self.is_connected():
            return {'error': self.last_error}
        
        try:
            try:
                ws = self.spreadsheet.worksheet('All Transactions')
            except:
                ws = self.spreadsheet.add_worksheet('All Transactions', 1000, 10)
            
            if clear_first:
                ws.clear()
            
            if ws.row_count == 0 or ws.cell(1, 1).value != 'Date':
                ws.update('A1:I1', [['Date', 'Post Date', 'Description', 'Amount', 
                                      'Category', 'Bank', 'Necessity', 'Recurrence', 'Note']])
            
            rows = []
            for t in transactions:
                rows.append([
                    t.transaction_date.strftime('%Y-%m-%d'),
                    t.post_date.strftime('%Y-%m-%d'),
                    t.description,
                    t.amount,
                    t.category,
                    t.bank,
                    t.necessity,
                    t.recurrence,
                    getattr(t, 'note', '')
                ])
            
            if rows:
                start = ws.row_count + 1 if not clear_first else 2
                ws.update(f'A{start}', rows)
            
            return {'synced_count': len(rows)}
        except Exception as e:
            return {'error': str(e)}
