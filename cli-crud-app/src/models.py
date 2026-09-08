"""
models.py
Defines the Contact data model used throughout the application.
Keeping the model separate from database and CLI logic follows the
Single Responsibility Principle and keeps the code modular.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Contact:
    """Represents a single contact record."""

    name: str
    email: str
    phone: str
    address: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_tuple(self):
        """Return field values as a tuple, useful for DB insert/update operations."""
        return (self.name, self.email, self.phone, self.address)

    def to_dict(self):
        """Return the contact as a dictionary (e.g. for display or export)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_row(row) -> "Contact":
        """Build a Contact instance from a database row (sqlite3.Row or tuple)."""
        return Contact(
            id=row[0],
            name=row[1],
            email=row[2],
            phone=row[3],
            address=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
