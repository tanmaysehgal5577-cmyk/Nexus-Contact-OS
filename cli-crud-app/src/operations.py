"""
operations.py
Implements the core CRUD (Create, Read, Update, Delete) + Search + Export/Import
business logic. This layer talks to the Database wrapper and returns Contact model
objects, keeping SQL out of the CLI layer entirely.
"""

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.database import Database
from src.exceptions import (
    ContactManagerError,
    DatabaseConnectionError,
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)
from src.models import Contact
from src.utils import (
    current_timestamp,
    validate_address,
    validate_email,
    validate_name,
    validate_phone,
)


class ContactRepository:
    """Encapsulates all CRUD and data management operations for Contact records."""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    # --------------------------------------------------------------- CREATE
    def create(self, contact: Contact) -> Contact:
        """Insert a new contact record. Raises DuplicateRecordError on email clash."""
        timestamp = current_timestamp()
        query = """
            INSERT INTO contacts (name, email, phone, address, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    query,
                    (*contact.to_tuple(), timestamp, timestamp),
                )
                conn.commit()
                contact.id = cursor.lastrowid
                contact.created_at = timestamp
                contact.updated_at = timestamp
                return contact
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError(
                f"A contact with email '{contact.email}' already exists."
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to create contact: {exc}") from exc

    # ----------------------------------------------------------------- READ
    def get_all(self, sort_by: str = "name", order: str = "asc") -> List[Contact]:
        """Return every contact, ordered by name, id, or created_at."""
        allowed_cols = {
            "name": "LOWER(name)",
            "id": "id",
            "created_at": "created_at",
        }
        col = allowed_cols.get(sort_by, "LOWER(name)")
        direction = "DESC" if order.lower() == "desc" else "ASC"
        query = f"SELECT * FROM contacts ORDER BY {col} {direction}"
        try:
            with self.db.get_connection() as conn:
                rows = conn.execute(query).fetchall()
                return [Contact.from_row(row) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to fetch contacts: {exc}") from exc

    def get_by_id(self, contact_id: int) -> Contact:
        """Return a single contact by ID. Raises RecordNotFoundError if missing."""
        query = "SELECT * FROM contacts WHERE id = ?"
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(query, (contact_id,)).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to fetch contact: {exc}") from exc

        if row is None:
            raise RecordNotFoundError(f"No contact found with ID {contact_id}.")
        return Contact.from_row(row)

    def search(self, keyword: str) -> List[Contact]:
        """Search contacts by name, email or phone (case-insensitive, partial match)."""
        query = """
            SELECT * FROM contacts
            WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR phone LIKE ?
            ORDER BY name ASC
        """
        pattern = f"%{keyword.lower()}%"
        try:
            with self.db.get_connection() as conn:
                rows = conn.execute(query, (pattern, pattern, pattern)).fetchall()
                return [Contact.from_row(row) for row in rows]
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Search failed: {exc}") from exc

    # ---------------------------------------------------------------- UPDATE
    def update(self, contact_id: int, contact: Contact) -> Contact:
        """Update an existing contact. Raises RecordNotFoundError if the ID does not exist."""
        self.get_by_id(contact_id)

        timestamp = current_timestamp()
        query = """
            UPDATE contacts
            SET name = ?, email = ?, phone = ?, address = ?, updated_at = ?
            WHERE id = ?
        """
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    query,
                    (*contact.to_tuple(), timestamp, contact_id),
                )
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DuplicateRecordError(
                f"Another contact already uses email '{contact.email}'."
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to update contact: {exc}") from exc

        return self.get_by_id(contact_id)

    # ---------------------------------------------------------------- DELETE
    def delete(self, contact_id: int) -> None:
        """Delete a contact by ID. Raises RecordNotFoundError if it doesn't exist."""
        self.get_by_id(contact_id)

        query = "DELETE FROM contacts WHERE id = ?"
        try:
            with self.db.get_connection() as conn:
                conn.execute(query, (contact_id,))
                conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to delete contact: {exc}") from exc

    # ----------------------------------------------------------------- MISC
    def count(self) -> int:
        """Return the total number of contacts stored."""
        query = "SELECT COUNT(*) FROM contacts"
        try:
            with self.db.get_connection() as conn:
                return conn.execute(query).fetchone()[0]
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to count contacts: {exc}") from exc

    def clear_all(self) -> int:
        """Delete all contacts from database and reset sequence."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("DELETE FROM contacts")
                deleted_count = cursor.rowcount
                try:
                    conn.execute("DELETE FROM sqlite_sequence WHERE name='contacts'")
                except sqlite3.OperationalError:
                    pass
                conn.commit()
                return deleted_count
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to clear database: {exc}") from exc

    def get_statistics(self) -> Dict[str, Any]:
        """Return overview statistics for the database."""
        total = self.count()
        if total == 0:
            return {
                "total": 0,
                "newest": None,
                "oldest": None,
            }

        try:
            with self.db.get_connection() as conn:
                newest_row = conn.execute(
                    "SELECT * FROM contacts ORDER BY id DESC LIMIT 1"
                ).fetchone()
                oldest_row = conn.execute(
                    "SELECT * FROM contacts ORDER BY id ASC LIMIT 1"
                ).fetchone()

                return {
                    "total": total,
                    "newest": Contact.from_row(newest_row) if newest_row else None,
                    "oldest": Contact.from_row(oldest_row) if oldest_row else None,
                }
        except sqlite3.Error as exc:
            raise DatabaseConnectionError(f"Failed to get statistics: {exc}") from exc

    # ---------------------------------------------------------- IMPORT / EXPORT
    def export_to_csv(self, filepath: str) -> int:
        """Export all contacts to a CSV file. Returns number of contacts exported."""
        contacts = self.get_all(sort_by="id", order="asc")
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["id", "name", "email", "phone", "address", "created_at", "updated_at"]
                )
                for c in contacts:
                    writer.writerow(
                        [
                            c.id,
                            c.name,
                            c.email,
                            c.phone,
                            c.address,
                            c.created_at,
                            c.updated_at,
                        ]
                    )
            return len(contacts)
        except OSError as exc:
            raise ContactManagerError(f"Failed to write CSV file: {exc}") from exc

    def export_to_json(self, filepath: str) -> int:
        """Export all contacts to a formatted JSON file."""
        contacts = self.get_all(sort_by="id", order="asc")
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = [c.to_dict() for c in contacts]
            with open(path, mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return len(contacts)
        except OSError as exc:
            raise ContactManagerError(f"Failed to write JSON file: {exc}") from exc

    def import_from_csv(self, filepath: str) -> Dict[str, int]:
        """Import contacts from a CSV file. Skips existing emails or invalid entries."""
        path = Path(filepath)
        if not path.is_file():
            raise RecordNotFoundError(f"File not found: '{filepath}'")

        imported = 0
        skipped = 0

        try:
            with open(path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name_raw = row.get("name") or row.get("Name")
                    email_raw = row.get("email") or row.get("Email")
                    phone_raw = row.get("phone") or row.get("Phone")
                    addr_raw = row.get("address") or row.get("Address", "")

                    if not (name_raw and email_raw and phone_raw):
                        skipped += 1
                        continue

                    try:
                        name = validate_name(name_raw)
                        email = validate_email(email_raw)
                        phone = validate_phone(phone_raw)
                        addr = validate_address(addr_raw)
                        self.create(
                            Contact(name=name, email=email, phone=phone, address=addr)
                        )
                        imported += 1
                    except (ValidationError, DuplicateRecordError):
                        skipped += 1

            return {"imported": imported, "skipped": skipped}
        except OSError as exc:
            raise ContactManagerError(f"Failed to read CSV file: {exc}") from exc

    def seed_sample_data(self) -> int:
        """Seed realistic sample contacts for quick demo and testing."""
        samples = [
            Contact(
                name="Aarav Sharma",
                email="aarav.sharma@example.com",
                phone="+91 98765 43210",
                address="Connaught Place, New Delhi",
            ),
            Contact(
                name="Priya Patel",
                email="priya.patel@example.com",
                phone="+91 98123 45678",
                address="Bandra West, Mumbai",
            ),
            Contact(
                name="Rohan Gupta",
                email="rohan.gupta@example.com",
                phone="+91 99887 76655",
                address="Indiranagar, Bengaluru",
            ),
            Contact(
                name="Ananya Verma",
                email="ananya.verma@example.com",
                phone="+91 91234 56789",
                address="Park Street, Kolkata",
            ),
            Contact(
                name="Vikram Singh",
                email="vikram.singh@example.com",
                phone="+91 97654 32109",
                address="Civil Lines, Jaipur",
            ),
        ]

        added = 0
        for contact in samples:
            try:
                self.create(contact)
                added += 1
            except DuplicateRecordError:
                pass
        return added
