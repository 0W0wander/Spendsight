"""
Expense Classifier - Multi-dimensional transaction categorization.

This module provides comprehensive classification of transactions beyond basic categories,
including:
- Needs vs Wants vs Savings (50/30/20 budgeting rule)
- Subscription and recurring expense detection
- Budget health analysis
"""
from typing import List, Dict, Set, Tuple
from backend.models.transaction import (
    Transaction, NecessityLevel, RecurrenceType
)


class ExpenseClassifier:
    """
    Classifies transactions with multiple dimensions for robust budgeting analysis.
    """
    
    # =========================================================================
    # SUBSCRIPTION DETECTION
    # =========================================================================
    
    # Known subscription services (lowercase for matching)
    SUBSCRIPTION_KEYWORDS: Set[str] = {
        # Streaming & Entertainment
        'netflix', 'hulu', 'disney+', 'disney plus', 'hbo max', 'hbo', 'paramount+',
        'peacock', 'apple tv', 'amazon prime', 'prime video', 'spotify', 'apple music',
        'youtube premium', 'youtube music', 'pandora', 'tidal', 'deezer', 'audible',
        'kindle unlimited', 'crunchyroll', 'funimation', 'espn+', 'sling', 'fubo',
        
        # Software & Productivity
        'microsoft 365', 'office 365', 'adobe', 'creative cloud', 'dropbox',
        'google one', 'icloud', 'evernote', 'notion', 'slack', 'zoom', 'canva',
        'grammarly', 'lastpass', '1password', 'dashlane', 'nordvpn', 'expressvpn',
        'surfshark', 'github', 'gitlab', 'jetbrains', 'figma', 'sketch',
        
        # Gaming
        'xbox game pass', 'playstation plus', 'ps plus', 'playstation network', 'psn',
        'nintendo online', 'ea play', 'ubisoft+', 'xbox live', 'steam',
        
        # News & Education
        'new york times', 'washington post', 'wall street journal', 'wsj',
        'the athletic', 'medium', 'substack', 'masterclass', 'skillshare',
        'coursera', 'udemy', 'linkedin learning', 'duolingo',
        
        # Fitness & Health
        'planet fitness', 'la fitness', 'equinox', 'orangetheory', 'peloton',
        'fitbit premium', 'headspace', 'calm', 'noom', 'weight watchers', 'ww',
        'myfitnesspal', 'strava',
        
        # Delivery & Food
        'doordash dashpass', 'uber one', 'uber eats pass', 'grubhub+',
        'instacart express', 'amazon fresh', 'hellofresh', 'blue apron',
        'factor', 'freshly', 'sunbasket',
        
        # Shopping & Memberships
        'amazon prime', 'costco membership', 'sam\'s club', 'bj\'s',
        'walmart+', 'target circle', 'shipt',
        
        # Other Services
        'patreon', 'onlyfans', 'twitch', 'discord nitro',
    }
    
    # =========================================================================
    # RECURRING EXPENSE PATTERNS (for recurrence detection)
    # =========================================================================
    
    RECURRING_EXPENSE_KEYWORDS: Set[str] = {
        # Housing
        'rent', 'mortgage', 'hoa', 'property tax', 'home insurance',
        'renters insurance', 'homeowners',
        
        # Loans
        'loan payment', 'student loan', 'auto loan', 'car payment',
        'navient', 'nelnet', 'great lakes', 'fedloan', 'sallie mae',
        
        # Insurance
        'insurance', 'geico', 'progressive', 'state farm', 'allstate',
        'liberty mutual', 'usaa', 'nationwide', 'farmers',
        'health insurance', 'dental', 'vision',
        
        # Utilities
        'electric', 'gas bill', 'water bill', 'sewer', 'trash',
        'internet', 'comcast', 'xfinity', 'spectrum', 'att', 'verizon',
        't-mobile', 'sprint', 'cricket',
        
        # Childcare
        'daycare', 'childcare', 'tuition',
    }
    
    # =========================================================================
    # ESSENTIAL/NEEDS CATEGORIES
    # =========================================================================
    
    ESSENTIAL_CATEGORIES: Set[str] = {
        'groceries', 'supermarkets', 'grocery',
        'utilities', 'bills & utilities',
        'healthcare', 'medical', 'pharmacy', 'health',
        'transportation', 'gas', 'gas & fuel', 'auto & transport',
        'housing', 'rent', 'mortgage',
        'insurance',
        'childcare', 'education',
    }
    
    ESSENTIAL_KEYWORDS: Set[str] = {
        # Food essentials
        'grocery', 'supermarket', 'whole foods', 'trader joe', 'safeway',
        'kroger', 'publix', 'aldi', 'lidl', 'food lion', 'wegmans',
        'harris teeter', 'stop & shop', 'giant', 'shoprite', 'meijer',
        'heb', 'costco', 'sam\'s club', 'bj\'s', 'walmart grocery',
        
        # Utilities
        'electric', 'gas bill', 'water', 'sewer', 'trash', 'utilities',
        
        # Healthcare
        'pharmacy', 'cvs', 'walgreens', 'rite aid', 'hospital', 'medical',
        'doctor', 'urgent care', 'dentist', 'optometrist', 'prescription',
        
        # Transportation (basic)
        'gas station', 'shell', 'exxon', 'chevron', 'bp', 'mobil',
        'metro', 'subway', 'bus', 'transit', 'uber', 'lyft',
        
        # Housing
        'rent', 'mortgage', 'property tax',
        
        # Insurance
        'insurance',
        
        # Childcare
        'daycare', 'childcare', 'school', 'tuition',
    }
    
    # =========================================================================
    # DISCRETIONARY/WANTS CATEGORIES
    # =========================================================================
    
    DISCRETIONARY_CATEGORIES: Set[str] = {
        'entertainment', 'food & dining', 'restaurants', 'shopping',
        'travel', 'travel/ entertainment', 'merchandise',
        'personal care', 'gifts', 'hobbies',
    }
    
    DISCRETIONARY_KEYWORDS: Set[str] = {
        # Dining out
        'restaurant', 'cafe', 'coffee', 'starbucks', 'dunkin', 'mcdonald',
        'burger', 'pizza', 'chipotle', 'taco bell', 'wendy\'s', 'chick-fil-a',
        'panera', 'subway', 'jimmy john', 'panda express', 'olive garden',
        'applebee', 'chili\'s', 'buffalo wild', 'ihop', 'denny\'s',
        'doordash', 'uber eats', 'grubhub', 'postmates', 'seamless',
        
        # Entertainment
        'movie', 'theater', 'cinema', 'amc', 'regal', 'concert', 'ticket',
        'ticketmaster', 'stubhub', 'live nation', 'bowling', 'arcade',
        'dave & buster', 'topgolf', 'escape room', 'museum', 'zoo',
        
        # Shopping
        'amazon', 'target', 'walmart', 'best buy', 'apple store',
        'nordstrom', 'macy\'s', 'bloomingdale', 'saks', 'neiman marcus',
        'tj maxx', 'marshalls', 'ross', 'home depot', 'lowe\'s', 'ikea',
        'wayfair', 'etsy', 'ebay', 'wish', 'shein', 'zara', 'h&m',
        'gap', 'old navy', 'banana republic', 'j.crew', 'uniqlo',
        
        # Personal care & beauty
        'salon', 'spa', 'massage', 'nail', 'barber', 'haircut',
        'sephora', 'ulta', 'bath & body',
        
        # Hobbies
        'hobby lobby', 'michaels', 'joann', 'guitar center',
        'dick\'s sporting', 'rei', 'bass pro', 'cabela',
        
        # Travel (leisure)
        'hotel', 'airbnb', 'vrbo', 'expedia', 'booking.com', 'kayak',
        'airline', 'delta', 'united', 'american airlines', 'southwest',
        'jetblue', 'spirit', 'frontier',
    }
    
    # =========================================================================
    # SAVINGS/INVESTMENT KEYWORDS
    # =========================================================================
    
    SAVINGS_KEYWORDS: Set[str] = {
        # Investments
        'vanguard', 'fidelity', 'schwab', 'td ameritrade', 'e*trade',
        'robinhood', 'webull', 'betterment', 'wealthfront', 'acorns',
        'stash', 'm1 finance', 'sofi invest',
        
        # Retirement
        '401k', 'ira', 'roth', 'retirement', 'pension',
        
        # Savings
        'savings transfer', 'emergency fund', 'high yield savings',
        'marcus', 'ally', 'discover savings', 'capital one savings',
        
        # Crypto
        'coinbase', 'binance', 'kraken', 'gemini', 'crypto.com',
    }
    
    # =========================================================================
    # CLASSIFICATION METHODS
    # =========================================================================
    
    @classmethod
    def classify(cls, transaction: Transaction) -> Transaction:
        """
        Apply all classification dimensions to a transaction.
        
        NOTE: Necessity (Needs/Wants/Savings) is intentionally NOT auto-classified
        during upload. Users should tag these manually for accuracy.
        
        Args:
            transaction: Transaction to classify
            
        Returns:
            Transaction with all classification fields populated
        """
        desc_lower = transaction.description.lower()
        
        # Income detection - income is not a necessity level (needs/wants/savings)
        # so we mark it as Unknown for necessity, but still classify recurrence
        if transaction.is_income:
            transaction.necessity = NecessityLevel.UNKNOWN  # Income isn't needs/wants/savings
            transaction.recurrence = cls._classify_recurrence(desc_lower, transaction.amount)
            return transaction
        
        # Classify recurrence
        transaction.recurrence = cls._classify_recurrence(desc_lower, transaction.amount)
        
        # Necessity is NOT auto-classified - leave as Unknown for user to tag manually
        transaction.necessity = NecessityLevel.UNKNOWN
        
        return transaction
    
    @classmethod
    def classify_batch(cls, transactions: List[Transaction]) -> List[Transaction]:
        """
        Classify a batch of transactions.
        
        Args:
            transactions: List of transactions to classify
            
        Returns:
            List of classified transactions
        """
        return [cls.classify(t) for t in transactions]
    
    @classmethod
    def _classify_necessity(cls, desc_lower: str, cat_lower: str) -> str:
        """Classify as Needs, Wants, or Savings based on 50/30/20 rule."""
        # Check for savings/investment
        for keyword in cls.SAVINGS_KEYWORDS:
            if keyword in desc_lower:
                return NecessityLevel.SAVINGS
        
        # Check for essential categories
        if cat_lower in cls.ESSENTIAL_CATEGORIES:
            return NecessityLevel.NEEDS
        
        # Check for essential keywords
        for keyword in cls.ESSENTIAL_KEYWORDS:
            if keyword in desc_lower:
                return NecessityLevel.NEEDS
        
        # Check for discretionary categories
        if cat_lower in cls.DISCRETIONARY_CATEGORIES:
            return NecessityLevel.WANTS
        
        # Check for discretionary keywords
        for keyword in cls.DISCRETIONARY_KEYWORDS:
            if keyword in desc_lower:
                return NecessityLevel.WANTS
        
        # Default to Unknown - let user or rules decide
        return NecessityLevel.UNKNOWN
    
    @classmethod
    def _classify_recurrence(cls, desc_lower: str, amount: float) -> str:
        """Determine if transaction is subscription, recurring, or one-time."""
        # Check for subscription keywords
        for keyword in cls.SUBSCRIPTION_KEYWORDS:
            if keyword in desc_lower:
                return RecurrenceType.SUBSCRIPTION
        
        # Check for recurring expense keywords
        for keyword in cls.RECURRING_EXPENSE_KEYWORDS:
            if keyword in desc_lower:
                return RecurrenceType.RECURRING
        
        # Default to one-time
        return RecurrenceType.ONE_TIME
    
    # =========================================================================
    # ANALYSIS METHODS
    # =========================================================================
    
    @classmethod
    def analyze_by_dimension(cls, transactions: List[Transaction]) -> Dict[str, Dict]:
        """
        Analyze spending across all classification dimensions.
        
        Returns:
            Dictionary with analysis for each dimension
        """
        # Filter to expenses only
        expenses = [t for t in transactions if t.is_expense]
        
        if not expenses:
            return {}
        
        total = sum(abs(t.amount) for t in expenses)
        
        return {
            'by_necessity': cls._group_and_sum(expenses, 'necessity', total),
            'by_recurrence': cls._group_and_sum(expenses, 'recurrence', total),
        }
    
    @classmethod
    def _group_and_sum(cls, transactions: List[Transaction], field: str, total: float) -> Dict:
        """Group transactions by a field and calculate totals."""
        groups: Dict[str, Dict] = {}
        
        for t in transactions:
            key = str(getattr(t, field))
            if key not in groups:
                groups[key] = {'total': 0, 'count': 0, 'transactions': []}
            groups[key]['total'] += abs(t.amount)
            groups[key]['count'] += 1
        
        # Calculate percentages and round
        for key in groups:
            groups[key]['total'] = round(groups[key]['total'], 2)
            groups[key]['percentage'] = round((groups[key]['total'] / total * 100), 1) if total > 0 else 0
            del groups[key]['transactions']  # Don't include full transaction objects
        
        return dict(sorted(groups.items(), key=lambda x: x[1]['total'], reverse=True))
    
    @classmethod
    def get_budget_health(cls, transactions: List[Transaction]) -> Dict:
        """
        Analyze budget health based on 50/30/20 rule.
        
        50% Needs (essential expenses)
        30% Wants (discretionary spending)
        20% Savings (financial goals)
        
        Returns:
            Dictionary with budget health metrics
        """
        expenses = [t for t in transactions if t.is_expense]
        
        if not expenses:
            return {'error': 'No expenses to analyze'}
        
        total = sum(abs(t.amount) for t in expenses)
        
        needs_total = sum(abs(t.amount) for t in expenses if t.necessity == NecessityLevel.NEEDS)
        wants_total = sum(abs(t.amount) for t in expenses if t.necessity == NecessityLevel.WANTS)
        savings_total = sum(abs(t.amount) for t in expenses if t.necessity == NecessityLevel.SAVINGS)
        
        needs_pct = (needs_total / total * 100) if total > 0 else 0
        wants_pct = (wants_total / total * 100) if total > 0 else 0
        savings_pct = (savings_total / total * 100) if total > 0 else 0
        
        # Determine health status
        needs_status = 'good' if needs_pct <= 55 else 'warning' if needs_pct <= 65 else 'critical'
        wants_status = 'good' if wants_pct <= 35 else 'warning' if wants_pct <= 45 else 'critical'
        savings_status = 'good' if savings_pct >= 15 else 'warning' if savings_pct >= 10 else 'critical'
        
        return {
            'total_spending': round(total, 2),
            'needs': {
                'total': round(needs_total, 2),
                'percentage': round(needs_pct, 1),
                'target': 50,
                'status': needs_status,
                'message': cls._get_needs_message(needs_pct)
            },
            'wants': {
                'total': round(wants_total, 2),
                'percentage': round(wants_pct, 1),
                'target': 30,
                'status': wants_status,
                'message': cls._get_wants_message(wants_pct)
            },
            'savings': {
                'total': round(savings_total, 2),
                'percentage': round(savings_pct, 1),
                'target': 20,
                'status': savings_status,
                'message': cls._get_savings_message(savings_pct)
            },
            'overall_health': cls._get_overall_health(needs_status, wants_status, savings_status)
        }
    
    @classmethod
    def _get_needs_message(cls, pct: float) -> str:
        if pct <= 50:
            return "Excellent! Your essential spending is well controlled."
        elif pct <= 55:
            return "Good, but watch for lifestyle creep in essentials."
        elif pct <= 65:
            return "Your needs are taking a bigger share. Look for savings."
        else:
            return "Essential costs are high. Consider reducing fixed expenses."
    
    @classmethod
    def _get_wants_message(cls, pct: float) -> str:
        if pct <= 30:
            return "Great balance! You're disciplined with discretionary spending."
        elif pct <= 35:
            return "Slightly over target. Small cuts can make a difference."
        elif pct <= 45:
            return "Discretionary spending is elevated. Review subscriptions."
        else:
            return "High discretionary spending. Identify areas to cut back."
    
    @classmethod
    def _get_savings_message(cls, pct: float) -> str:
        if pct >= 20:
            return "Excellent! You're on track for financial security."
        elif pct >= 15:
            return "Good progress, but try to increase savings slightly."
        elif pct >= 10:
            return "Below target. Try to automate more savings."
        else:
            return "Low savings rate. Consider the 'pay yourself first' approach."
    
    @classmethod
    def _get_overall_health(cls, needs: str, wants: str, savings: str) -> str:
        scores = {'good': 3, 'warning': 2, 'critical': 1}
        total_score = scores[needs] + scores[wants] + scores[savings]
        
        if total_score >= 8:
            return "Excellent"
        elif total_score >= 6:
            return "Good"
        elif total_score >= 4:
            return "Needs Improvement"
        else:
            return "Critical"
    
    @classmethod
    def get_subscription_summary(cls, transactions: List[Transaction]) -> Dict:
        """
        Get summary of subscription expenses.
        
        Returns:
            Dictionary with subscription analysis
        """
        subscriptions = [t for t in transactions if t.recurrence == RecurrenceType.SUBSCRIPTION and t.is_expense]
        
        if not subscriptions:
            return {'total': 0, 'count': 0, 'monthly_estimate': 0, 'subscriptions': []}
        
        # Group by description to find unique subscriptions
        sub_groups: Dict[str, Dict] = {}
        
        for t in subscriptions:
            key = t.description
            if key not in sub_groups:
                sub_groups[key] = {
                    'name': t.description,
                    'total': 0,
                    'count': 0,
                    'amounts': [],
                    'category': t.category
                }
            sub_groups[key]['total'] += abs(t.amount)
            sub_groups[key]['count'] += 1
            sub_groups[key]['amounts'].append(abs(t.amount))
        
        # Calculate typical monthly amount
        subscription_list = []
        for name, data in sub_groups.items():
            avg_amount = data['total'] / data['count']
            subscription_list.append({
                'name': name,
                'average_amount': round(avg_amount, 2),
                'occurrences': data['count'],
                'total_spent': round(data['total'], 2),
                'category': data['category']
            })
        
        # Sort by total spent
        subscription_list.sort(key=lambda x: x['total_spent'], reverse=True)
        
        total = sum(abs(t.amount) for t in subscriptions)
        
        return {
            'total': round(total, 2),
            'count': len(subscription_list),
            'monthly_estimate': round(sum(s['average_amount'] for s in subscription_list), 2),
            'annual_estimate': round(sum(s['average_amount'] for s in subscription_list) * 12, 2),
            'subscriptions': subscription_list
        }
    
    @classmethod
    def get_reduction_opportunities(cls, transactions: List[Transaction]) -> List[Dict]:
        """
        Identify opportunities to reduce spending.
        
        Returns:
            List of reduction opportunities with potential savings
        """
        expenses = [t for t in transactions if t.is_expense]
        
        opportunities = []
        
        # 1. Subscriptions
        subscriptions = [t for t in expenses if t.recurrence == RecurrenceType.SUBSCRIPTION]
        if subscriptions:
            sub_total = sum(abs(t.amount) for t in subscriptions)
            if len(set(t.description for t in subscriptions)) > 3:  # Multiple subscriptions
                opportunities.append({
                    'category': 'Subscriptions',
                    'current': round(sub_total, 2),
                    'potential_savings': round(sub_total * 0.3, 2),  # Cancel 30%
                    'suggestion': 'Review and cancel unused subscriptions',
                    'priority': 'High'
                })
        
        # 2. Dining out
        dining = [t for t in expenses if 'restaurant' in t.category.lower() or 'dining' in t.category.lower() 
                  or any(kw in t.description.lower() for kw in ['restaurant', 'cafe', 'doordash', 'uber eats', 'grubhub'])]
        if dining:
            dining_total = sum(abs(t.amount) for t in dining)
            if dining_total > 200:
                opportunities.append({
                    'category': 'Dining Out',
                    'current': round(dining_total, 2),
                    'potential_savings': round(dining_total * 0.5, 2),  # Cook more at home
                    'suggestion': 'Cook more meals at home',
                    'priority': 'High'
                })
        
        # 3. Entertainment
        entertainment = [t for t in expenses if 'entertainment' in t.category.lower()]
        if entertainment:
            ent_total = sum(abs(t.amount) for t in entertainment)
            if ent_total > 100:
                opportunities.append({
                    'category': 'Entertainment',
                    'current': round(ent_total, 2),
                    'potential_savings': round(ent_total * 0.25, 2),
                    'suggestion': 'Look for free or low-cost entertainment alternatives',
                    'priority': 'Low'
                })
        
        # Sort by potential savings
        opportunities.sort(key=lambda x: x['potential_savings'], reverse=True)
        
        return opportunities

