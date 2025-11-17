import pandas as pd
from enum import Enum

class CSVType(Enum):
    CHASE_CREDIT = "chase_credit"
    CHASE_DEBIT = "chase_debit"
    DISCOVER = "discover"
    UNKNOWN = "unknown"

class CSVDetector:
    @staticmethod
    def detect(filepath):
        df = pd.read_csv(filepath, nrows=1)
        cols = set(df.columns)
        
        if {'Transaction Date', 'Post Date', 'Description', 'Amount'}.issubset(cols):
            return CSVType.CHASE_CREDIT
        if {'Posting Date', 'Description', 'Amount', 'Balance'}.issubset(cols):
            return CSVType.CHASE_DEBIT
        if {'Trans. Date', 'Description', 'Amount'}.issubset(cols):
            return CSVType.DISCOVER
        
        return CSVType.UNKNOWN
