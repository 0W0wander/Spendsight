"""Generate spending insights."""
from typing import List, Dict
from backend.models.transaction import Transaction
from backend.analytics.categorizer import TransactionCategorizer

class InsightsGenerator:
    """Generate intelligent insights from transaction data."""
    
    @staticmethod
    def generate_insights(transactions: List[Transaction]) -> List[Dict[str, str]]:
        """
        Generate actionable insights from transactions.
        
        Returns:
            List of insight dictionaries with type and message
        """
        if not transactions:
            return [{'type': 'info', 'message': 'No transactions to analyze yet. Upload some CSVs to get started!'}]
        
        insights = []
        
        # Calculate basic metrics
        total_spent = sum(abs(t.amount) for t in transactions if t.is_expense)
        total_income = sum(t.amount for t in transactions if t.is_income)
        expense_transactions = [t for t in transactions if t.is_expense]
        
        # Insight 1: Overall spending
        if expense_transactions:
            avg_transaction = total_spent / len(expense_transactions)
            insights.append({
                'type': 'summary',
                'icon': '',
                'title': 'Overall Spending',
                'message': f'You spent ${total_spent:,.2f} across {len(expense_transactions)} transactions. Average transaction: ${avg_transaction:.2f}'
            })
        
        # Insight 2: Savings rate
        if total_income > 0:
            savings_rate = ((total_income - total_spent) / total_income) * 100
            insights.append({
                'type': 'savings',
                'icon': '',
                'title': 'Savings Rate',
                'message': f'Your savings rate is {savings_rate:.1f}%. {"Great job!" if savings_rate > 20 else "Keep it up!" if savings_rate > 10 else "Consider reducing expenses."}'
            })
        
        # Insight 3: Top spending category
        categories = TransactionCategorizer.categorize_by_spending(expense_transactions)
        if categories:
            top_category = list(categories.items())[0]
            insights.append({
                'type': 'category',
                'icon': '',
                'title': 'Top Spending Category',
                'message': f'{top_category[0]}: ${top_category[1]["total"]:,.2f} ({top_category[1]["percentage"]}% of total spending)'
            })
        
        # Insight 4: Large transactions
        large_transactions = [t for t in expense_transactions if abs(t.amount) > 500]
        if large_transactions:
            insights.append({
                'type': 'alert',
                'icon': '',
                'title': 'Large Transactions',
                'message': f'You have {len(large_transactions)} transactions over $500. Total: ${sum(abs(t.amount) for t in large_transactions):,.2f}'
            })
        
        # Insight 5: Recurring transactions
        recurring = TransactionCategorizer.detect_recurring(transactions)
        if recurring:
            total_recurring = sum(abs(r['amount']) * r['frequency'] for r in recurring)
            insights.append({
                'type': 'recurring',
                'icon': '',
                'title': 'Recurring Transactions',
                'message': f'Detected {len(recurring)} recurring charges totaling ${total_recurring:,.2f}'
            })
        
        # Insight 6: Monthly trend
        monthly_data = TransactionCategorizer.monthly_trends(transactions)
        if len(monthly_data) >= 2:
            months = sorted(monthly_data.keys())
            latest = monthly_data[months[-1]]
            previous = monthly_data[months[-2]]
            
            change = ((latest['spent'] - previous['spent']) / previous['spent']) * 100 if previous['spent'] > 0 else 0
            insights.append({
                'type': 'trend',
                'icon': '',
                'title': 'Monthly Trend',
                'message': f'Spending {"increased" if change > 0 else "decreased"} by {abs(change):.1f}% compared to last month'
            })
        
        # Insight 7: Top merchant
        merchants = TransactionCategorizer.analyze_merchants(expense_transactions, top_n=1)
        if merchants:
            top_merchant = merchants[0]
            insights.append({
                'type': 'merchant',
                'icon': '',
                'title': 'Top Merchant',
                'message': f'{top_merchant["merchant"]}: ${top_merchant["total"]:,.2f} ({top_merchant["count"]} transactions)'
            })
        
        return insights
    
    @staticmethod
    def get_budget_recommendations(transactions: List[Transaction]) -> Dict[str, float]:
        """
        Generate budget recommendations based on spending patterns.
        
        Returns:
            Dictionary with recommended budgets per category
        """
        expense_transactions = [t for t in transactions if t.is_expense]
        categories = TransactionCategorizer.categorize_by_spending(expense_transactions)
        
        # Calculate monthly averages
        monthly_data = TransactionCategorizer.monthly_trends(transactions)
        months_count = len(monthly_data) if monthly_data else 1
        
        recommendations = {}
        for category, data in categories.items():
            # Recommend 110% of average spending (10% buffer)
            monthly_avg = data['total'] / months_count
            recommendations[category] = round(monthly_avg * 1.1, 2)
        
        return recommendations

