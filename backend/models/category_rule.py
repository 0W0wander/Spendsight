"""Category rule model for keyword-based auto-tagging."""
from dataclasses import dataclass, field as dataclass_field
from typing import List, Dict, Optional
import json
from pathlib import Path
import uuid


@dataclass
class CategoryRule:
    """
    Represents a rule for auto-categorizing transactions based on keywords.
    
    A rule matches when ALL keywords are present in the transaction description.
    Matching is case-insensitive.
    
    Supports multiple tags: e.g., set category, necessity, and recurrence at once.
    """
    id: str
    category: str  # The value to assign (legacy field, used for backward compatibility)
    keywords: List[str]  # ALL keywords must be present (AND logic)
    priority: int = 0  # Higher priority rules are checked first
    enabled: bool = True
    field: str = 'category'  # Which field to update (legacy, used for backward compatibility)
    tags: Dict[str, str] = dataclass_field(default_factory=dict)  # Multiple field:value pairs, e.g., {'category': 'Hobby', 'necessity': 'Wants', 'recurrence': 'Subscription'}
    
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
        # Build tags from legacy fields if tags is empty
        tags = self.tags if self.tags else {self.field: self.category}
        return {
            'id': self.id,
            'category': self.category,
            'keywords': self.keywords,
            'priority': self.priority,
            'enabled': self.enabled,
            'field': self.field,
            'tags': tags
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CategoryRule':
        """Create rule from dictionary."""
        tags = data.get('tags', {})
        # For backward compatibility: if no tags, create from legacy fields
        if not tags and 'category' in data and 'field' in data:
            tags = {data.get('field', 'category'): data['category']}
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            category=data.get('category', ''),
            keywords=data.get('keywords', []),
            priority=data.get('priority', 0),
            enabled=data.get('enabled', True),
            field=data.get('field', 'category'),
            tags=tags
        )


class CategoryRuleEngine:
    """
    Engine for managing and applying category rules to transactions.
    """
    
    def __init__(self, storage_path: Path = None):
        """
        Initialize the rule engine.
        
        Args:
            storage_path: Path to store rules persistently (JSON file)
        """
        self.rules: List[CategoryRule] = []
        self.storage_path = storage_path or Path(__file__).resolve().parent.parent.parent / 'data' / 'category_rules.json'
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rules = [CategoryRule.from_dict(r) for r in data.get('rules', [])]
            except Exception as e:
                print(f"Error loading category rules: {e}")
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
            print(f"Error saving category rules: {e}")
    
    def add_rule(self, category: str, keywords: List[str], priority: int = 0, field: str = 'category', tags: Dict[str, str] = None) -> CategoryRule:
        """
        Add a new category rule.
        
        Args:
            category: The value to assign when rule matches (legacy, for backward compatibility)
            keywords: List of keywords that must ALL be present
            priority: Higher priority rules are checked first
            field: Which field to update (legacy, for backward compatibility)
            tags: Dict of field:value pairs (e.g., {'category': 'Hobby', 'necessity': 'Wants'})
            
        Returns:
            The created CategoryRule
        """
        # Build tags dict - use provided tags or create from legacy fields
        if tags is None:
            tags = {field: category} if category else {}
        
        rule = CategoryRule(
            id=str(uuid.uuid4()),
            category=category,
            keywords=keywords,
            priority=priority,
            enabled=True,
            field=field,
            tags=tags
        )
        self.rules.append(rule)
        # Sort by priority (descending)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self._save_rules()
        return rule
    
    def update_rule(self, rule_id: str, category: str = None, keywords: List[str] = None, 
                   priority: int = None, enabled: bool = None) -> CategoryRule:
        """
        Update an existing rule.
        
        Args:
            rule_id: ID of the rule to update
            category: New category (optional)
            keywords: New keywords list (optional)
            priority: New priority (optional)
            enabled: Enable/disable rule (optional)
            
        Returns:
            The updated CategoryRule or None if not found
        """
        for rule in self.rules:
            if rule.id == rule_id:
                if category is not None:
                    rule.category = category
                if keywords is not None:
                    rule.keywords = keywords
                if priority is not None:
                    rule.priority = priority
                if enabled is not None:
                    rule.enabled = enabled
                
                # Re-sort by priority
                self.rules.sort(key=lambda r: r.priority, reverse=True)
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
    
    def get_rule(self, rule_id: str) -> CategoryRule:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def get_all_rules(self) -> List[CategoryRule]:
        """Get all rules sorted by priority."""
        return self.rules
    
    def find_matching_category(self, description: str) -> str:
        """
        Find the category for a description based on rules.
        
        The first matching rule (highest priority) wins.
        
        Args:
            description: The transaction description
            
        Returns:
            The category from the matching rule, or None if no match
        """
        for rule in self.rules:
            if rule.matches(description):
                return rule.category
        return None
    
    def apply_to_transaction(self, transaction) -> bool:
        """
        Apply rules to a single transaction.
        
        If matching rules are found, updates the appropriate transaction fields.
        Supports multiple tags per rule (e.g., category + necessity + recurrence).
        
        Args:
            transaction: Transaction object with description and various attributes
            
        Returns:
            True if any field was updated, False otherwise
        """
        updated = False
        for rule in self.rules:
            if rule.matches(transaction.description):
                # Apply all tags from the rule
                tags = rule.tags if rule.tags else {rule.field or 'category': rule.category}
                for field, value in tags.items():
                    if hasattr(transaction, field) and value:
                        setattr(transaction, field, value)
                        updated = True
        return updated
    
    def apply_to_all(self, transactions: list) -> int:
        """
        Apply rules to all transactions.
        
        Args:
            transactions: List of Transaction objects
            
        Returns:
            Number of transactions that were updated
        """
        updated_count = 0
        for transaction in transactions:
            if self.apply_to_transaction(transaction):
                updated_count += 1
        return updated_count
    
    def apply_single_rule(self, rule: CategoryRule, transactions: list) -> int:
        """
        Apply a single rule to all transactions.
        
        Supports multiple tags per rule (e.g., category + necessity + recurrence).
        
        Args:
            rule: The rule to apply
            transactions: List of Transaction objects
            
        Returns:
            Number of transactions that were updated
        """
        updated_count = 0
        # Use tags if available, otherwise fall back to legacy field/category
        tags = rule.tags if rule.tags else {rule.field or 'category': rule.category}
        
        for transaction in transactions:
            if rule.matches(transaction.description):
                transaction_updated = False
                for field, value in tags.items():
                    if hasattr(transaction, field) and value:
                        setattr(transaction, field, value)
                        transaction_updated = True
                if transaction_updated:
                    updated_count += 1
        return updated_count


# Global instance for the application
rule_engine = CategoryRuleEngine()

