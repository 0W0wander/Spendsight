"""Transaction categorization and analysis."""
from typing import List, Dict
from collections import defaultdict
from datetime import datetime, timedelta
from backend.models.transaction import Transaction

class TransactionCategorizer:
    """Categorize and analyze transactions."""
    
    # Merchant to category mapping (can be extended)
    MERCHANT_CATEGORIES = {
        # Food & Dining
        'restaurant': 'Food & Dining',
        'cafe': 'Food & Dining',
        'coffee': 'Food & Dining',
        'starbucks': 'Food & Dining',
        'mcdonald': 'Food & Dining',
        'pizza': 'Food & Dining',
        'grocery': 'Groceries',
        'market': 'Groceries',
        'whole foods': 'Groceries',
        'trader joe': 'Groceries',
        'safeway': 'Groceries',
        'kroger': 'Groceries',
        'walmart': 'Groceries',
        
        # Transportation
        'uber': 'Transportation',
        'lyft': 'Transportation',
        'gas': 'Transportation',
        'shell': 'Transportation',
        'chevron': 'Transportation',
        'parking': 'Transportation',
        
        # Shopping
        'amazon': 'Shopping',
        'target': 'Shopping',
        'costco': 'Shopping',
        
        # Entertainment
        'netflix': 'Entertainment',
        'spotify': 'Entertainment',
        'hulu': 'Entertainment',
        'disney': 'Entertainment',
        'movie': 'Entertainment',
        'theater': 'Entertainment',
        
        # Utilities
        'electric': 'Utilities',
        'water': 'Utilities',
        'internet': 'Utilities',
        'phone': 'Utilities',
        'verizon': 'Utilities',
        'at&t': 'Utilities',
        't-mobile': 'Utilities',
        
        # Health
        'pharmacy': 'Health',
        'cvs': 'Health',
        'walgreens': 'Health',
        'medical': 'Health',
        'doctor': 'Health',
        'hospital': 'Health',
    }
    
    # Category colors for charts
    CATEGORY_COLORS = {
        'Food & Dining': '#FF6384',
        'Groceries': '#36A2EB',
        'Transportation': '#FFCE56',
        'Shopping': '#4BC0C0',
        'Entertainment': '#9966FF',
        'Utilities': '#FF9F40',
        'Health': '#C9CBCF',
        'Travel': '#7C4DFF',
        'Education': '#00BCD4',
        'Other': '#607D8B',
    }
    
    @staticmethod
    def categorize_by_spending(transactions: List[Transaction]) -> Dict[str, Dict]:
        """
        Categorize transactions by spending amount.
        
        Returns:
            Dictionary with category breakdowns
        """
        category_data = defaultdict(lambda: {'total': 0, 'count': 0, 'transactions': []})
        
        for transaction in transactions:
            if transaction.is_expense:
                category = transaction.category
                amount = abs(transaction.amount)
                
                category_data[category]['total'] += amount
                category_data[category]['count'] += 1
                category_data[category]['transactions'].append(transaction)
        
        # Sort by total spending
        sorted_categories = dict(
            sorted(
                category_data.items(),
                key=lambda x: x[1]['total'],
                reverse=True
            )
        )
        
        # Calculate percentages
        total_spending = sum(data['total'] for data in category_data.values())
        
        result = {}
        for category, data in sorted_categories.items():
            result[category] = {
                'total': round(data['total'], 2),
                'count': data['count'],
                'average': round(data['total'] / data['count'], 2),
                'percentage': round((data['total'] / total_spending * 100), 1) if total_spending > 0 else 0
            }
        
        return result
    
    @staticmethod
    def analyze_merchants(transactions: List[Transaction], top_n: int = 10) -> List[Dict]:
        """
        Analyze top merchants by spending.
        
        Args:
            transactions: List of transactions
            top_n: Number of top merchants to return
            
        Returns:
            List of top merchants with spending data
        """
        merchant_data = defaultdict(lambda: {'total': 0, 'count': 0})
        
        for transaction in transactions:
            if transaction.is_expense:
                merchant = transaction.description
                amount = abs(transaction.amount)
                
                merchant_data[merchant]['total'] += amount
                merchant_data[merchant]['count'] += 1
        
        # Sort and get top N
        top_merchants = sorted(
            merchant_data.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )[:top_n]
        
        return [
            {
                'merchant': merchant,
                'total': round(data['total'], 2),
                'count': data['count'],
                'average': round(data['total'] / data['count'], 2)
            }
            for merchant, data in top_merchants
        ]
    
    @staticmethod
    def detect_recurring(transactions: List[Transaction]) -> List[Dict]:
        """
        Detect recurring transactions (simplified version).
        
        Returns:
            List of potential recurring transactions
        """
        # Group by description and amount
        transaction_groups = defaultdict(list)
        
        for transaction in transactions:
            key = (transaction.description, round(transaction.amount, 2))
            transaction_groups[key].append(transaction)
        
        # Find recurring (appears 3+ times)
        recurring = []
        for (description, amount), trans_list in transaction_groups.items():
            if len(trans_list) >= 3:
                recurring.append({
                    'description': description,
                    'amount': amount,
                    'frequency': len(trans_list),
                    'category': trans_list[0].category
                })
        
        return sorted(recurring, key=lambda x: x['frequency'], reverse=True)
    
    @staticmethod
    def monthly_trends(transactions: List[Transaction]) -> Dict[str, Dict]:
        """
        Calculate monthly spending trends.
        
        Returns:
            Dictionary with monthly spending data
        """
        monthly_data = defaultdict(lambda: {
            'spent': 0,
            'income': 0,
            'transactions': 0,
            'categories': defaultdict(float),
            'necessity': defaultdict(float),
            'recurrence': defaultdict(float),
            'bank': defaultdict(float)
        })
        
        for transaction in transactions:
            month = transaction.month_year
            
            if transaction.is_expense:
                amount = abs(transaction.amount)
                monthly_data[month]['spent'] += amount
                monthly_data[month]['categories'][transaction.category] += amount
                monthly_data[month]['bank'][transaction.bank.title()] += amount
                # Get necessity and recurrence from transaction (can be enum or string)
                necessity = getattr(transaction, 'necessity', None)
                if necessity:
                    nec_val = necessity.value if hasattr(necessity, 'value') else necessity
                    monthly_data[month]['necessity'][nec_val] += amount
                recurrence = getattr(transaction, 'recurrence', None)
                if recurrence:
                    rec_val = recurrence.value if hasattr(recurrence, 'value') else recurrence
                    monthly_data[month]['recurrence'][rec_val] += amount
            else:
                monthly_data[month]['income'] += transaction.amount
            
            monthly_data[month]['transactions'] += 1
        
        # Format results
        result = {}
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            result[month] = {
                'spent': round(data['spent'], 2),
                'income': round(data['income'], 2),
                'net': round(data['income'] - data['spent'], 2),
                'transactions': data['transactions'],
                'top_category': max(data['categories'].items(), key=lambda x: x[1])[0] if data['categories'] else 'N/A',
                'categories': {k: round(v, 2) for k, v in data['categories'].items()},
                'necessity': {k: round(v, 2) for k, v in data['necessity'].items()},
                'recurrence': {k: round(v, 2) for k, v in data['recurrence'].items()},
                'bank': {k: round(v, 2) for k, v in data['bank'].items()}
            }
        
        return result
    
    @staticmethod
    def weekly_spending(transactions: List[Transaction]) -> Dict[str, Dict]:
        """
        Calculate weekly spending breakdown.
        
        Returns:
            Dictionary with weekly spending data keyed by week start date
        """
        weekly_data = defaultdict(lambda: {
            'spent': 0,
            'income': 0,
            'transactions': 0,
            'categories': defaultdict(float),
            'necessity': defaultdict(float),
            'recurrence': defaultdict(float),
            'bank': defaultdict(float)
        })
        
        for transaction in transactions:
            # Get the Monday of the transaction's week
            date = transaction.transaction_date
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            
            if transaction.is_expense:
                amount = abs(transaction.amount)
                weekly_data[week_key]['spent'] += amount
                weekly_data[week_key]['categories'][transaction.category] += amount
                weekly_data[week_key]['bank'][transaction.bank.title()] += amount
                # Get necessity and recurrence from transaction (can be enum or string)
                necessity = getattr(transaction, 'necessity', None)
                if necessity:
                    nec_val = necessity.value if hasattr(necessity, 'value') else necessity
                    weekly_data[week_key]['necessity'][nec_val] += amount
                recurrence = getattr(transaction, 'recurrence', None)
                if recurrence:
                    rec_val = recurrence.value if hasattr(recurrence, 'value') else recurrence
                    weekly_data[week_key]['recurrence'][rec_val] += amount
            else:
                weekly_data[week_key]['income'] += transaction.amount
            
            weekly_data[week_key]['transactions'] += 1
        
        # Format and sort results
        result = {}
        for week in sorted(weekly_data.keys(), reverse=True):
            data = weekly_data[week]
            result[week] = {
                'spent': round(data['spent'], 2),
                'income': round(data['income'], 2),
                'net': round(data['income'] - data['spent'], 2),
                'transactions': data['transactions'],
                'categories': {k: round(v, 2) for k, v in data['categories'].items()},
                'necessity': {k: round(v, 2) for k, v in data['necessity'].items()},
                'recurrence': {k: round(v, 2) for k, v in data['recurrence'].items()},
                'bank': {k: round(v, 2) for k, v in data['bank'].items()},
                'daily_avg': round(data['spent'] / 7, 2)
            }
        
        return result
    
    @staticmethod
    def daily_spending(transactions: List[Transaction], days: int = 30) -> Dict[str, Dict]:
        """
        Calculate daily spending for the last N days.
        
        Args:
            transactions: List of transactions
            days: Number of days to analyze (default 30)
            
        Returns:
            Dictionary with daily spending data including category, necessity, and recurrence breakdowns
        """
        daily_data = defaultdict(lambda: {
            'spent': 0, 
            'income': 0, 
            'transactions': 0,
            'categories': defaultdict(float),
            'necessity': defaultdict(float),
            'recurrence': defaultdict(float),
            'bank': defaultdict(float)
        })
        
        # Get date range
        if transactions:
            max_date = max(t.transaction_date for t in transactions)
            min_date = max_date - timedelta(days=days)
        else:
            return {}
        
        for transaction in transactions:
            if transaction.transaction_date >= min_date:
                date_key = transaction.transaction_date.strftime('%Y-%m-%d')
                
                if transaction.is_expense:
                    amount = abs(transaction.amount)
                    daily_data[date_key]['spent'] += amount
                    daily_data[date_key]['categories'][transaction.category] += amount
                    daily_data[date_key]['bank'][transaction.bank.title()] += amount
                    # Get necessity and recurrence from transaction (can be enum or string)
                    necessity = getattr(transaction, 'necessity', None)
                    if necessity:
                        nec_val = necessity.value if hasattr(necessity, 'value') else necessity
                        daily_data[date_key]['necessity'][nec_val] += amount
                    recurrence = getattr(transaction, 'recurrence', None)
                    if recurrence:
                        rec_val = recurrence.value if hasattr(recurrence, 'value') else recurrence
                        daily_data[date_key]['recurrence'][rec_val] += amount
                else:
                    daily_data[date_key]['income'] += transaction.amount
                
                daily_data[date_key]['transactions'] += 1
        
        # Fill in missing days with zeros
        result = {}
        current_date = min_date
        while current_date <= max_date:
            date_key = current_date.strftime('%Y-%m-%d')
            if date_key in daily_data:
                result[date_key] = {
                    'spent': round(daily_data[date_key]['spent'], 2),
                    'income': round(daily_data[date_key]['income'], 2),
                    'transactions': daily_data[date_key]['transactions'],
                    'categories': {k: round(v, 2) for k, v in daily_data[date_key]['categories'].items()},
                    'necessity': {k: round(v, 2) for k, v in daily_data[date_key]['necessity'].items()},
                    'recurrence': {k: round(v, 2) for k, v in daily_data[date_key]['recurrence'].items()},
                    'bank': {k: round(v, 2) for k, v in daily_data[date_key]['bank'].items()}
                }
            else:
                result[date_key] = {'spent': 0, 'income': 0, 'transactions': 0, 'categories': {}, 'necessity': {}, 'recurrence': {}, 'bank': {}}
            current_date += timedelta(days=1)
        
        return result
    
    @staticmethod
    def day_of_week_analysis(transactions: List[Transaction]) -> Dict[str, Dict]:
        """
        Analyze spending patterns by day of week.
        
        Returns:
            Dictionary with spending by day of week (0=Monday, 6=Sunday)
        """
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_data = {day: {'spent': 0, 'count': 0, 'transactions': []} for day in days}
        
        for transaction in transactions:
            if transaction.is_expense:
                day_name = days[transaction.transaction_date.weekday()]
                day_data[day_name]['spent'] += abs(transaction.amount)
                day_data[day_name]['count'] += 1
                day_data[day_name]['transactions'].append(transaction)
        
        # Calculate averages and percentages
        total_spent = sum(d['spent'] for d in day_data.values())
        
        result = {}
        for day in days:
            data = day_data[day]
            result[day] = {
                'total': round(data['spent'], 2),
                'count': data['count'],
                'average': round(data['spent'] / data['count'], 2) if data['count'] > 0 else 0,
                'percentage': round((data['spent'] / total_spent) * 100, 1) if total_spent > 0 else 0
            }
        
        return result
    
    @staticmethod
    def spending_by_bank(transactions: List[Transaction]) -> Dict[str, Dict]:
        """
        Analyze spending by bank source.
        
        Returns:
            Dictionary with spending breakdown by bank
        """
        bank_data = defaultdict(lambda: {'spent': 0, 'income': 0, 'count': 0})
        
        for transaction in transactions:
            bank = transaction.bank.title()
            if transaction.is_expense:
                bank_data[bank]['spent'] += abs(transaction.amount)
            else:
                bank_data[bank]['income'] += transaction.amount
            bank_data[bank]['count'] += 1
        
        total_spent = sum(d['spent'] for d in bank_data.values())
        
        result = {}
        for bank, data in bank_data.items():
            result[bank] = {
                'spent': round(data['spent'], 2),
                'income': round(data['income'], 2),
                'count': data['count'],
                'percentage': round((data['spent'] / total_spent) * 100, 1) if total_spent > 0 else 0
            }
        
        return result
    
    @staticmethod
    def spending_velocity(transactions: List[Transaction]) -> Dict[str, float]:
        """
        Calculate spending velocity metrics.
        
        Returns:
            Dictionary with spending rate metrics
        """
        expense_transactions = [t for t in transactions if t.is_expense]
        
        if not expense_transactions:
            return {
                'daily_avg': 0,
                'weekly_avg': 0,
                'monthly_avg': 0,
                'per_transaction_avg': 0,
                'highest_single_day': 0,
                'highest_single_day_date': None
            }
        
        # Get date range
        dates = [t.transaction_date for t in expense_transactions]
        min_date, max_date = min(dates), max(dates)
        total_days = max((max_date - min_date).days, 1)
        
        total_spent = sum(abs(t.amount) for t in expense_transactions)
        
        # Find highest spending day
        daily_totals = defaultdict(float)
        for t in expense_transactions:
            daily_totals[t.transaction_date.strftime('%Y-%m-%d')] += abs(t.amount)
        
        if daily_totals:
            highest_day = max(daily_totals.items(), key=lambda x: x[1])
        else:
            highest_day = (None, 0)
        
        return {
            'daily_avg': round(total_spent / total_days, 2),
            'weekly_avg': round((total_spent / total_days) * 7, 2),
            'monthly_avg': round((total_spent / total_days) * 30, 2),
            'per_transaction_avg': round(total_spent / len(expense_transactions), 2),
            'highest_single_day': round(highest_day[1], 2),
            'highest_single_day_date': highest_day[0]
        }
    
    @staticmethod
    def category_trends(transactions: List[Transaction]) -> Dict[str, Dict]:
        """
        Analyze category spending trends over time (by month).
        
        Returns:
            Dictionary with category spending by month
        """
        # Group by category and month
        category_monthly = defaultdict(lambda: defaultdict(float))
        
        for transaction in transactions:
            if transaction.is_expense:
                month = transaction.month_year
                category = transaction.category
                category_monthly[category][month] += abs(transaction.amount)
        
        # Get all months
        all_months = set()
        for category_data in category_monthly.values():
            all_months.update(category_data.keys())
        all_months = sorted(all_months)
        
        # Format result with all months filled
        result = {}
        for category, monthly_data in category_monthly.items():
            result[category] = {
                'months': all_months,
                'values': [round(monthly_data.get(m, 0), 2) for m in all_months],
                'total': round(sum(monthly_data.values()), 2),
                'color': TransactionCategorizer.CATEGORY_COLORS.get(category, '#607D8B')
            }
        
        return result
    
    @staticmethod
    def get_top_spending_days(transactions: List[Transaction], top_n: int = 10) -> List[Dict]:
        """
        Get the top spending days.
        
        Args:
            transactions: List of transactions
            top_n: Number of top days to return
            
        Returns:
            List of top spending days with details
        """
        daily_data = defaultdict(lambda: {'total': 0, 'transactions': [], 'categories': defaultdict(float)})
        
        for transaction in transactions:
            if transaction.is_expense:
                date_key = transaction.transaction_date.strftime('%Y-%m-%d')
                amount = abs(transaction.amount)
                daily_data[date_key]['total'] += amount
                daily_data[date_key]['transactions'].append(transaction)
                daily_data[date_key]['categories'][transaction.category] += amount
        
        # Sort by total and get top N
        sorted_days = sorted(daily_data.items(), key=lambda x: x[1]['total'], reverse=True)[:top_n]
        
        result = []
        for date, data in sorted_days:
            top_category = max(data['categories'].items(), key=lambda x: x[1])[0] if data['categories'] else 'N/A'
            result.append({
                'date': date,
                'total': round(data['total'], 2),
                'transaction_count': len(data['transactions']),
                'top_category': top_category,
                'weekday': datetime.strptime(date, '%Y-%m-%d').strftime('%A')
            })
        
        return result
    
    @staticmethod
    def get_statistics(transactions: List[Transaction]) -> Dict:
        """
        Calculate comprehensive spending statistics.
        
        Returns:
            Dictionary with various statistical metrics
        """
        expense_transactions = [t for t in transactions if t.is_expense]
        
        if not expense_transactions:
            return {
                'count': 0,
                'total': 0,
                'mean': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'std_dev': 0
            }
        
        amounts = [abs(t.amount) for t in expense_transactions]
        n = len(amounts)
        
        # Calculate statistics
        total = sum(amounts)
        mean = total / n
        
        # Median
        sorted_amounts = sorted(amounts)
        if n % 2 == 0:
            median = (sorted_amounts[n//2 - 1] + sorted_amounts[n//2]) / 2
        else:
            median = sorted_amounts[n//2]
        
        # Standard deviation
        variance = sum((x - mean) ** 2 for x in amounts) / n
        std_dev = variance ** 0.5
        
        return {
            'count': n,
            'total': round(total, 2),
            'mean': round(mean, 2),
            'median': round(median, 2),
            'min': round(min(amounts), 2),
            'max': round(max(amounts), 2),
            'std_dev': round(std_dev, 2)
        }

