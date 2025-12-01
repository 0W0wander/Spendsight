"""Period notes model for storing personal analysis per week/month."""
from dataclasses import dataclass
from typing import Dict, Optional
import json
from pathlib import Path


@dataclass
class PeriodNote:
    """
    Represents a personal analysis note for a specific period (week or month).
    
    The period_key format:
    - Weekly: "weekly_2024-01-07" (using the Sunday of that week)
    - Monthly: "monthly_2024-01" (year-month)
    """
    period_key: str
    content: str
    
    def to_dict(self) -> dict:
        """Convert note to dictionary."""
        return {
            'period_key': self.period_key,
            'content': self.content
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PeriodNote':
        """Create note from dictionary."""
        return cls(
            period_key=data['period_key'],
            content=data.get('content', '')
        )


class PeriodNotesEngine:
    """
    Engine for managing personal analysis notes per period.
    """
    
    def __init__(self, storage_path: Path = None):
        """
        Initialize the notes engine.
        
        Args:
            storage_path: Path to store notes persistently (JSON file)
        """
        self.notes: Dict[str, PeriodNote] = {}
        self.storage_path = storage_path or Path(__file__).resolve().parent.parent.parent / 'data' / 'period_notes.json'
        self._load_notes()
    
    def _load_notes(self):
        """Load notes from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for note_data in data.get('notes', []):
                        note = PeriodNote.from_dict(note_data)
                        self.notes[note.period_key] = note
            except Exception as e:
                print(f"Error loading period notes: {e}")
                self.notes = {}
        else:
            self.notes = {}
    
    def _save_notes(self):
        """Save notes to storage file."""
        try:
            # Ensure data directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'notes': [n.to_dict() for n in self.notes.values()]
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving period notes: {e}")
    
    def get_note(self, period_key: str) -> Optional[str]:
        """
        Get note content for a specific period.
        
        Args:
            period_key: The period identifier (e.g., "weekly_2024-01-07" or "monthly_2024-01")
            
        Returns:
            The note content or empty string if not found
        """
        note = self.notes.get(period_key)
        return note.content if note else ''
    
    def save_note(self, period_key: str, content: str) -> PeriodNote:
        """
        Save or update a note for a specific period.
        
        Args:
            period_key: The period identifier
            content: The note content
            
        Returns:
            The saved PeriodNote
        """
        note = PeriodNote(period_key=period_key, content=content)
        self.notes[period_key] = note
        self._save_notes()
        return note
    
    def delete_note(self, period_key: str) -> bool:
        """
        Delete a note for a specific period.
        
        Args:
            period_key: The period identifier
            
        Returns:
            True if deleted, False if not found
        """
        if period_key in self.notes:
            del self.notes[period_key]
            self._save_notes()
            return True
        return False
    
    def get_all_notes(self) -> Dict[str, str]:
        """
        Get all notes as a dictionary.
        
        Returns:
            Dictionary mapping period_key to content
        """
        return {key: note.content for key, note in self.notes.items()}


# Global instance for the application
period_notes_engine = PeriodNotesEngine()

