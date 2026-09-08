"""
test_app.py
Unit tests for the Contact Manager application.
Run with:  python -m unittest discover -s tests
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is on sys.path whether executed from root or tests dir
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.database import Database
from src.exceptions import DuplicateRecordError, RecordNotFoundError, ValidationError
from src.models import Contact
from src.operations import ContactRepository
from src.utils import validate_email, validate_name, validate_phone


class TestValidation(unittest.TestCase):
    def test_valid_name(self):
        self.assertEqual(validate_name("  John Doe  "), "John Doe")

    def test_invalid_name_too_short(self):
        with self.assertRaises(ValidationError):
            validate_name("J")

    def test_invalid_name_numbers(self):
        with self.assertRaises(ValidationError):
            validate_name("John123")

    def test_valid_email(self):
        self.assertEqual(validate_email("Test@Example.com"), "test@example.com")

    def test_invalid_email(self):
        with self.assertRaises(ValidationError):
            validate_email("not-an-email")

    def test_valid_phone(self):
        self.assertEqual(validate_phone("+91 98765 43210"), "+91 98765 43210")

    def test_invalid_phone(self):
        with self.assertRaises(ValidationError):
            validate_phone("abc")


class TestContactRepository(unittest.TestCase):
    def setUp(self):
        # Use a temporary database file for isolated, repeatable tests.
        self.tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_file.close()
        self.db = Database(db_path=self.tmp_file.name)
        self.repo = ContactRepository(self.db)

    def tearDown(self):
        if os.path.exists(self.tmp_file.name):
            os.unlink(self.tmp_file.name)

    def test_create_and_get_contact(self):
        contact = Contact(name="Jane Doe", email="jane@example.com", phone="1234567890")
        saved = self.repo.create(contact)
        self.assertIsNotNone(saved.id)

        fetched = self.repo.get_by_id(saved.id)
        self.assertEqual(fetched.name, "Jane Doe")
        self.assertEqual(fetched.email, "jane@example.com")

    def test_duplicate_email_raises(self):
        c1 = Contact(name="Jane Doe", email="dup@example.com", phone="1234567890")
        c2 = Contact(name="John Roe", email="dup@example.com", phone="0987654321")
        self.repo.create(c1)
        with self.assertRaises(DuplicateRecordError):
            self.repo.create(c2)

    def test_get_nonexistent_contact_raises(self):
        with self.assertRaises(RecordNotFoundError):
            self.repo.get_by_id(9999)

    def test_update_contact(self):
        contact = Contact(name="Jane Doe", email="jane2@example.com", phone="1234567890")
        saved = self.repo.create(contact)

        updated_data = Contact(
            name="Jane Updated", email="jane2@example.com", phone="1111111111"
        )
        result = self.repo.update(saved.id, updated_data)
        self.assertEqual(result.name, "Jane Updated")
        self.assertEqual(result.phone, "1111111111")

    def test_delete_contact(self):
        contact = Contact(name="Delete Me", email="delete@example.com", phone="1234567890")
        saved = self.repo.create(contact)
        self.repo.delete(saved.id)
        with self.assertRaises(RecordNotFoundError):
            self.repo.get_by_id(saved.id)

    def test_search_contacts(self):
        self.repo.create(Contact(name="Alice Smith", email="alice@example.com", phone="1112223333"))
        self.repo.create(Contact(name="Bob Jones", email="bob@example.com", phone="4445556666"))

        results = self.repo.search("alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Alice Smith")

    def test_get_all_and_count(self):
        self.repo.create(Contact(name="Alice Smith", email="a1@example.com", phone="1112223333"))
        self.repo.create(Contact(name="Bob Jones", email="b1@example.com", phone="4445556666"))
        self.assertEqual(self.repo.count(), 2)
        self.assertEqual(len(self.repo.get_all()), 2)

    def test_sorting(self):
        self.repo.create(Contact(name="Zara Alpha", email="zara@example.com", phone="1111111111"))
        self.repo.create(Contact(name="Adam Beta", email="adam@example.com", phone="2222222222"))

        contacts_name = self.repo.get_all(sort_by="name", order="asc")
        self.assertEqual(contacts_name[0].name, "Adam Beta")
        self.assertEqual(contacts_name[1].name, "Zara Alpha")

        contacts_id_desc = self.repo.get_all(sort_by="id", order="desc")
        self.assertEqual(contacts_id_desc[0].name, "Adam Beta")

    def test_seed_sample_data(self):
        added = self.repo.seed_sample_data()
        self.assertGreater(added, 0)
        self.assertEqual(self.repo.count(), added)

        # Calling again should not create duplicates
        second_run = self.repo.seed_sample_data()
        self.assertEqual(second_run, 0)

    def test_export_and_import_csv(self):
        self.repo.create(Contact(name="Test User", email="testuser@example.com", phone="9998887776"))
        csv_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        csv_file.close()

        try:
            exported_count = self.repo.export_to_csv(csv_file.name)
            self.assertEqual(exported_count, 1)

            # Clear DB and reimport
            self.repo.clear_all()
            self.assertEqual(self.repo.count(), 0)

            import_res = self.repo.import_from_csv(csv_file.name)
            self.assertEqual(import_res["imported"], 1)
            self.assertEqual(import_res["skipped"], 0)
            self.assertEqual(self.repo.count(), 1)
        finally:
            if os.path.exists(csv_file.name):
                os.unlink(csv_file.name)

    def test_export_json(self):
        self.repo.create(Contact(name="JSON User", email="json@example.com", phone="8887776665"))
        json_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        json_file.close()

        try:
            count = self.repo.export_to_json(json_file.name)
            self.assertEqual(count, 1)
            with open(json_file.name, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["name"], "JSON User")
        finally:
            if os.path.exists(json_file.name):
                os.unlink(json_file.name)

    def test_statistics_and_clear(self):
        self.repo.create(Contact(name="First User", email="first@example.com", phone="1231231234"))
        self.repo.create(Contact(name="Second User", email="second@example.com", phone="2342342345"))

        stats = self.repo.get_statistics()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["oldest"].name, "First User")
        self.assertEqual(stats["newest"].name, "Second User")

        deleted = self.repo.clear_all()
        self.assertEqual(deleted, 2)
        self.assertEqual(self.repo.count(), 0)


if __name__ == "__main__":
    unittest.main()
