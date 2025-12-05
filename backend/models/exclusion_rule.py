"""Exclusion rule model for sweep/removal of transactions based on keywords."""
from dataclasses import dataclass, field
from typing import List
import json
from pathlib import Path
import uuid


@dataclass
class ExclusionRule:
    """
    Represents a rule for excluding/sweeping transactions based on keywords.
    
    A rule matches when ALL keywords are present in the transaction description.
    Matching is case-insensitive.
    Matching transactions will be removed from view and excluded from future uploads.
    """
    id: str
    keywords: List[str]  # ALL keywords must be present (AND logic)
    title: str = ""  # Optional title/name for the rule
    enabled: bool = True
    swept_count: int = 0  # Track how many transactions this rule has swept
    
    def matches(self, description: str) -> bool:
        """
        Check if this rule matches the given description.
        
        All keywords must be present (AND logic).
        Matching is case-insensitive.
        
        Args:
            description: The transaction description to check
            
        Returns:
            True if all keywords are found in the description
        """
        if not self.enabled:
            return False
        
        desc_lower = description.lower()
        return all(keyword.lower() in desc_lower for keyword in self.keywords)
    
    def to_dict(self) -> dict:
        """Convert rule to dictionary."""
        return {
            'id': self.id,
            'keywords': self.keywords,
            'title': self.title,
            'enabled': self.enabled,
            'swept_count': self.swept_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExclusionRule':
        """Create rule from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            keywords=data['keywords'],
            title=data.get('title', ''),
            enabled=data.get('enabled', True),
            swept_count=data.get('swept_count', 0)
        )


class ExclusionRuleEngine:
    """
    Engine for managing and applying exclusion/sweep rules to transactions.
    """
    
    def __init__(self, storage_path: Path = None):
        """
        Initialize the exclusion rule engine.
        
        Args:
            storage_path: Path to store rules persistently (JSON file)
        """
        self.rules: List[ExclusionRule] = []
        self.storage_path = storage_path or Path(__file__).resolve().parent.parent.parent / 'data' / 'exclusion_rules.json'
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rules = [ExclusionRule.from_dict(r) for r in data.get('rules', [])]
            except Exception as e:
                print(f"Error loading exclusion rules: {e}")
                self.rules = []
        else:
            self.rules = []
    
    def _save_rules(self):
        """Save rules to storage file."""
        try:
            # Ensure data directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'rules': [r.to_dict() for r in self.rules]
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving exclusion rules: {e}")
    
    def add_rule(self, keywords: List[str], title: str = "") -> ExclusionRule:
        """
        Add a new exclusion rule.
        
        Args:
            keywords: List of keywords that must ALL be present to match
            title: Optional title/name for the rule
            
        Returns:
            The created ExclusionRule
        """
        rule = ExclusionRule(
            id=str(uuid.uuid4()),
            keywords=keywords,
            title=title,
            enabled=True,
            swept_count=0
        )
        self.rules.append(rule)
        self._save_rules()
        return rule
    
    def update_rule(self, rule_id: str, keywords: List[str] = None, 
                   title: str = None, enabled: bool = None) -> ExclusionRule:
        """
        Update an existing rule.
        
        Args:
            rule_id: ID of the rule to update
            keywords: New keywords list (optional)
            title: New title (optional)
            enabled: Enable/disable rule (optional)
            
        Returns:
            The updated ExclusionRule or None if not found
        """
        for rule in self.rules:
            if rule.id == rule_id:
                if keywords is not None:
                    rule.keywords = keywords
                if title is not None:
                    rule.title = title
                if enabled is not None:
                    rule.enabled = enabled
                
                self._save_rules()
                return rule
        return None
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a rule by ID.
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            True if deleted, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                del self.rules[i]
                self._save_rules()
                return True
        return False
    
    def get_rule(self, rule_id: str) -> ExclusionRule:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def get_all_rules(self) -> List[ExclusionRule]:
        """Get all rules."""
        return self.rules
    
    def should_exclude(self, description: str) -> bool:
        """
        Check if a transaction with the given description should be excluded.
        
        Args:
            description: The transaction description
            
        Returns:
            True if any enabled rule matches, False otherwise
        """
        for rule in self.rules:
            if rule.matches(description):
                return True
        return False
    
    def sweep_transactions(self, transactions: list) -> tuple:
        """
        Remove transactions that match any exclusion rule.
        
        Args:
            transactions: List of Transaction objects
            
        Returns:
            Tuple of (remaining_transactions, swept_count)
        """
        remaining = []
        swept_count = 0
        
        # Track counts per rule for updating swept_count
        rule_match_counts = {rule.id: 0 for rule in self.rules}
        
        for transaction in transactions:
            excluded = False
            for rule in self.rules:
                if rule.matches(transaction.description):
                    rule_match_counts[rule.id] += 1
                    excluded = True
                    break
            
            if excluded:
                swept_count += 1
            else:
                remaining.append(transaction)
        
        # Update swept counts on rules
        for rule in self.rules:
            if rule_match_counts[rule.id] > 0:
                rule.swept_count += rule_match_counts[rule.id]
        
        if swept_count > 0:
            self._save_rules()
        
        return remaining, swept_count
    
    def filter_new_transactions(self, transactions: list) -> tuple:
        """
        Filter out transactions that match exclusion rules from a new upload.
        
        Args:
            transactions: List of Transaction objects from a new CSV upload
            
        Returns:
            Tuple of (filtered_transactions, excluded_count)
        """
        return self.sweep_transactions(transactions)
    
    def count_matches(self, keywords: List[str], transactions: list) -> tuple:
        """
        Count how many transactions would match the given keywords.
        
        Args:
            keywords: List of keywords to check
            transactions: List of Transaction objects
            
        Returns:
            Tuple of (count, all_matching_descriptions)
        """
        count = 0
        matches = []
        
        for transaction in transactions:
            desc_lower = transaction.description.lower()
            if all(kw.lower() in desc_lower for kw in keywords):
                count += 1
                # Include all matching transaction descriptions (truncated for display)
                matches.append(transaction.description[:80] + ('...' if len(transaction.description) > 80 else ''))
        
        return count, matches


# Global instance for the application
exclusion_engine = ExclusionRuleEngine()

