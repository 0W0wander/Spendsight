"""CSV auto-detector for identifying bank/card type from CSV columns."""
import os
import pandas as pd
from typing import Tuple, Optional
from enum import Enum


class CSVType(Enum):
    """Enum for different CSV types."""
    CHASE_CREDIT = "chase_credit"
    CHASE_DEBIT = "chase_debit"
    DISCOVER = "discover"
    TD_CHECKING = "td_checking"
    TD_CREDIT = "td_credit"
    UNKNOWN = "unknown"


class CSVDetector:
    """
    Detects the bank and card type from CSV file columns.
    
    Uses column matching to identify the source of the CSV file.
    The detector looks for characteristic columns unique to each format.
    """
    
    # Column signatures for each CSV type
    # Each format has required columns and optional columns
    
    # Chase Credit Card: Transaction Date, Post Date, Description, Category, Type, Amount, Memo
    CHASE_CREDIT_COLUMNS = {
        'required': {'Transaction Date', 'Post Date', 'Description', 'Amount'},
        'characteristic': {'Category', 'Memo'},  # These distinguish it from other formats
        'all': {'Transaction Date', 'Post Date', 'Description', 'Category', 'Type', 'Amount', 'Memo'}
    }
    
    # Chase Debit/Checking: Details, Posting Date, Description, Amount, Type, Balance, Check or Slip #
    CHASE_DEBIT_COLUMNS = {
        'required': {'Posting Date', 'Description', 'Amount'},
        'characteristic': {'Details', 'Balance'},  # These distinguish it from other formats
        'all': {'Details', 'Posting Date', 'Description', 'Amount', 'Type', 'Balance', 'Check or Slip #'}
    }
    
    # Discover: Trans. Date, Post Date, Description, Amount, Category
    DISCOVER_COLUMNS = {
        'required': {'Description', 'Amount'},
        'characteristic': {'Trans. Date'},  # The period in "Trans." distinguishes it
        'all': {'Trans. Date', 'Post Date', 'Description', 'Amount', 'Category'}
    }

    # TD Bank checking & credit share the same export columns
    # Date, Bank RTN, Account Number, Transaction Type, Description, Debit, Credit, Check Number, Account Running Balance
    TD_COLUMNS = {
        'required': {'Date', 'Description', 'Debit', 'Credit'},
        'characteristic': {'Bank RTN', 'Account Running Balance'},
        'all': {
            'Date', 'Bank RTN', 'Account Number', 'Transaction Type',
            'Description', 'Debit', 'Credit', 'Check Number', 'Account Running Balance'
        }
    }
    
    @classmethod
    def detect(cls, file_path: str) -> Tuple[CSVType, float, bool]:
        """
        Detect the type of CSV file based on its columns.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (CSVType, confidence_score, has_categories)
            - CSVType: The detected type of CSV
            - confidence_score: 0.0-1.0 indicating how confident the detection is
            - has_categories: Whether this CSV format includes a Category column
        """
        try:
            # Read just the header row
            df = pd.read_csv(file_path, nrows=0, index_col=False)
            columns = {str(c).strip() for c in df.columns}
            
            csv_type, confidence, has_categories = cls._detect_from_columns(columns)

            # TD checking and credit share columns — use filename to distinguish
            if csv_type in (CSVType.TD_CHECKING, CSVType.TD_CREDIT):
                csv_type = cls._td_subtype_from_filename(file_path)

            return csv_type, confidence, has_categories
            
        except Exception as e:
            return CSVType.UNKNOWN, 0.0, False
    
    @classmethod
    def detect_from_dataframe(cls, df: pd.DataFrame, file_path: Optional[str] = None) -> Tuple[CSVType, float, bool]:
        """
        Detect the type of CSV from an already-loaded DataFrame.
        
        Args:
            df: Pandas DataFrame with CSV data
            file_path: Optional path used to distinguish TD checking vs credit
            
        Returns:
            Tuple of (CSVType, confidence_score, has_categories)
        """
        columns = {str(c).strip() for c in df.columns}
        csv_type, confidence, has_categories = cls._detect_from_columns(columns)
        if csv_type in (CSVType.TD_CHECKING, CSVType.TD_CREDIT) and file_path:
            csv_type = cls._td_subtype_from_filename(file_path)
        return csv_type, confidence, has_categories

    @classmethod
    def _td_subtype_from_filename(cls, file_path: str) -> CSVType:
        """
        Distinguish TD checking vs credit using the filename.

        TD uses the same column layout for both account types, so filename
        hints (e.g. 'Credit card.csv', 'Checking acct.csv') are the signal.
        Defaults to checking when ambiguous.
        """
        name = os.path.basename(file_path).lower().replace('_', ' ').replace('-', ' ')
        credit_hints = ('credit', ' cc ', 'cc.', 'card')
        checking_hints = ('checking', 'check', 'debit', 'savings', 'acct', 'dda')

        if any(h.strip() in name for h in credit_hints):
            # Prefer credit when both could match (e.g. unlikely), but 'card' alone is enough
            if 'checking' not in name and 'debit' not in name:
                return CSVType.TD_CREDIT
        if any(h in name for h in checking_hints):
            return CSVType.TD_CHECKING
        if any(h.strip() in name for h in credit_hints):
            return CSVType.TD_CREDIT
        return CSVType.TD_CHECKING
    
    @classmethod
    def _detect_from_columns(cls, columns: set) -> Tuple[CSVType, float, bool]:
        """
        Core detection logic based on column names.
        
        Uses a scoring system:
        - Each matching required column adds points
        - Each matching characteristic column adds bonus points
        - The format with the highest score wins
        
        Args:
            columns: Set of column names from the CSV
            
        Returns:
            Tuple of (CSVType, confidence_score, has_categories)
        """
        scores = {}
        
        # Score Chase Credit
        scores[CSVType.CHASE_CREDIT] = cls._calculate_score(
            columns, 
            cls.CHASE_CREDIT_COLUMNS['required'],
            cls.CHASE_CREDIT_COLUMNS['characteristic'],
            cls.CHASE_CREDIT_COLUMNS['all']
        )
        
        # Score Chase Debit
        scores[CSVType.CHASE_DEBIT] = cls._calculate_score(
            columns,
            cls.CHASE_DEBIT_COLUMNS['required'],
            cls.CHASE_DEBIT_COLUMNS['characteristic'],
            cls.CHASE_DEBIT_COLUMNS['all']
        )
        
        # Score Discover
        scores[CSVType.DISCOVER] = cls._calculate_score(
            columns,
            cls.DISCOVER_COLUMNS['required'],
            cls.DISCOVER_COLUMNS['characteristic'],
            cls.DISCOVER_COLUMNS['all']
        )

        # Score TD Bank (checking/credit share columns; subtype resolved via filename)
        td_score = cls._calculate_score(
            columns,
            cls.TD_COLUMNS['required'],
            cls.TD_COLUMNS['characteristic'],
            cls.TD_COLUMNS['all']
        )
        scores[CSVType.TD_CHECKING] = td_score
        scores[CSVType.TD_CREDIT] = td_score
        
        # Find the best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # If best score is too low, return unknown
        if best_score < 0.5:
            return CSVType.UNKNOWN, best_score, False
        
        # Determine if this format has categories
        has_categories = best_type in [CSVType.CHASE_CREDIT, CSVType.DISCOVER]
        
        return best_type, best_score, has_categories
    
    @classmethod
    def _calculate_score(cls, columns: set, required: set, characteristic: set, all_cols: set) -> float:
        """
        Calculate a match score for a given column signature.
        
        Args:
            columns: Actual columns in the CSV
            required: Required columns for this format
            characteristic: Columns that are unique to this format
            all_cols: All possible columns for this format
            
        Returns:
            Score from 0.0 to 1.0
        """
        # Count matching required columns
        required_matches = len(columns & required)
        required_total = len(required)
        
        # Count matching characteristic columns (these are weighted more heavily)
        char_matches = len(columns & characteristic)
        char_total = len(characteristic)
        
        # Count total column matches
        all_matches = len(columns & all_cols)
        all_total = len(all_cols)
        
        # If we don't have all required columns, significantly penalize
        if required_matches < required_total:
            required_score = required_matches / required_total * 0.5
        else:
            required_score = 1.0
        
        # Characteristic columns are very important for disambiguation
        char_score = char_matches / char_total if char_total > 0 else 0
        
        # Overall column match percentage
        all_score = all_matches / all_total if all_total > 0 else 0
        
        # Weighted combination:
        # - 40% weight on required columns being present
        # - 40% weight on characteristic (unique) columns
        # - 20% weight on overall column match
        final_score = (required_score * 0.4) + (char_score * 0.4) + (all_score * 0.2)
        
        return final_score
    
    @classmethod
    def get_format_info(cls, csv_type: CSVType) -> dict:
        """
        Get information about a detected CSV format.
        
        Args:
            csv_type: The detected CSV type
            
        Returns:
            Dictionary with format information
        """
        info = {
            CSVType.CHASE_CREDIT: {
                'name': 'Chase Credit Card',
                'bank': 'chase',
                'card_type': 'credit',
                'has_categories': True,
                'description': 'Chase credit card transaction export'
            },
            CSVType.CHASE_DEBIT: {
                'name': 'Chase Debit/Checking',
                'bank': 'chase',
                'card_type': 'debit',
                'has_categories': False,
                'description': 'Chase checking/savings account transaction export'
            },
            CSVType.DISCOVER: {
                'name': 'Discover Credit Card',
                'bank': 'discover',
                'card_type': 'credit',
                'has_categories': True,
                'description': 'Discover credit card transaction export'
            },
            CSVType.TD_CHECKING: {
                'name': 'TD Bank Checking',
                'bank': 'td',
                'card_type': 'debit',
                'has_categories': False,
                'description': 'TD Bank checking/savings account transaction export'
            },
            CSVType.TD_CREDIT: {
                'name': 'TD Bank Credit Card',
                'bank': 'td',
                'card_type': 'credit',
                'has_categories': False,
                'description': 'TD Bank credit card transaction export'
            },
            CSVType.UNKNOWN: {
                'name': 'Unknown Format',
                'bank': 'unknown',
                'card_type': 'unknown',
                'has_categories': False,
                'description': 'Could not determine the CSV format'
            }
        }
        
        return info.get(csv_type, info[CSVType.UNKNOWN])
