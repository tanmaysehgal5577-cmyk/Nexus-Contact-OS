"""
cli.py
The interactive Command Line Interface for Contact Manager.
Provides an aesthetically pleasing terminal UI with ANSI colors,
smart input-validation retry loops, table formatters, and full CRUD + Export/Import.
"""

import sys
from pathlib import Path

from src.exceptions import (
    ContactManagerError,
    DatabaseConnectionError,
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)
from src.models import Contact
from src.operations import ContactRepository
from src.utils import (
    Color,
    current_timestamp,
    error,
    highlight,
    info,
    init_terminal,
    success,
    truncate,
    validate_address,
    validate_email,
    validate_name,
    validate_non_empty_int,
    validate_phone,
    warning,
)


class ContactManagerCLI:
    """Drives the interactive menu loop and CRUD interactions."""

    def __init__(self, repository: ContactRepository = None):
        init_terminal()
        self.repo = repository or ContactRepository()
        self.menu_actions = {
            "1": self.create_contact,
            "2": self.list_contacts,
            "3": self.view_contact,
            "4": self.update_contact,
            "5": self.delete_contact,
            "6": self.search_contacts,
            "7": self.export_contacts,
            "8": self.import_contacts,
            "9": self.seed_sample_data,
            "10": self.show_statistics,
            "11": self.clear_database,
            "12": self.launch_gui,
        }

    # ------------------------------------------------------------- RUN LOOP
    def run(self):
        """Main application loop."""
        self.print_welcome()
        while True:
            self.print_menu()
            try:
                choice = input(f"{Color.BOLD}Enter your choice [0-11]: {Color.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{info('Application interrupted. Goodbye!')}")
                break

            if choice == "0":
                print(f"\n{Color.CYAN}{Color.BOLD}Thank you for using Contact Manager. Goodbye!{Color.RESET}\n")
                break

            action = self.menu_actions.get(choice)
            if not action:
                print(f"\n{error('Invalid choice. Please select an option from the menu.')}\n")
                continue

            try:
                action()
            except KeyboardInterrupt:
                print(f"\n\n{warning('Operation cancelled by user.')}\n")
            except ValidationError as exc:
                print(f"\n{error(f'Validation Error: {exc}')}\n")
            except RecordNotFoundError as exc:
                print(f"\n{error(f'Not Found: {exc}')}\n")
            except DuplicateRecordError as exc:
                print(f"\n{warning(f'Duplicate: {exc}')}\n")
            except DatabaseConnectionError as exc:
                print(f"\n{error(f'Database Error: {exc}')}\n")
            except ContactManagerError as exc:
                print(f"\n{error(f'Application Error: {exc}')}\n")
            except Exception as exc:  # noqa: BLE001
                print(f"\n{error(f'Unexpected error occurred: {exc}')}\n")

    # ------------------------------------------------------------- UI HELPERS
    def print_welcome(self):
        banner = f"""
{Color.CYAN}{Color.BOLD}+======================================================================+
|                    CONTACT MANAGER CLI SYSTEM                        |
|                 SQLite Fast CRUD | Import/Export                     |
+======================================================================+{Color.RESET}"""
        print(banner)

    def print_menu(self):
        total = self.repo.count()
        count_badge = f"{Color.MAGENTA}(Total Contacts: {total}){Color.RESET}"
        print(f"\n{Color.BOLD}======================== MAIN MENU ========================{Color.RESET} {count_badge}")
        print(f"  {Color.GREEN}1.{Color.RESET} Create a new contact")
        print(f"  {Color.GREEN}2.{Color.RESET} List all contacts (with sort)")
        print(f"  {Color.GREEN}3.{Color.RESET} View contact details by ID")
        print(f"  {Color.GREEN}4.{Color.RESET} Update contact")
        print(f"  {Color.GREEN}5.{Color.RESET} Delete contact")
        print(f"  {Color.GREEN}6.{Color.RESET} Search contacts (Name, Email, Phone)")
        print(f"  {Color.YELLOW}7.{Color.RESET} Export contacts (CSV / JSON)")
        print(f"  {Color.YELLOW}8.{Color.RESET} Import contacts from CSV")
        print(f"  {Color.CYAN}9.{Color.RESET} Populate sample demo contacts")
        print(f"  {Color.CYAN}10.{Color.RESET} View database statistics & summary")
        print(f"  {Color.RED}11.{Color.RESET} Clear all contacts (Reset)")
        print(f"  {Color.MAGENTA}12.{Color.RESET} Launch NexusContact Web GUI (Browser)")
        print(f"  {Color.DIM}0.{Color.RESET} Exit")
        print(f"{Color.BOLD}--------------------------------------------------------{Color.RESET}")

    def prompt_field(self, field_name: str, validator, optional: bool = False, default: str = "") -> str:
        """Prompt user repeatedly until valid input or cancel 'q'."""
        hint = f" [{default}]" if default else (" (optional)" if optional else "")
        prompt_text = f"{Color.BOLD}{field_name}{hint}: {Color.RESET}"

        while True:
            try:
                val = input(prompt_text).strip()
            except (KeyboardInterrupt, EOFError):
                raise KeyboardInterrupt

            if not val and default:
                return default
            if not val and optional:
                return ""
            if val.lower() in ("q", "cancel"):
                raise KeyboardInterrupt

            try:
                return validator(val)
            except ValidationError as exc:
                print(f"  {error(str(exc))} {Color.DIM}(or type 'cancel' to exit){Color.RESET}")

    def print_table(self, contacts):
        if not contacts:
            print(f"\n{info('No contacts found.')}\n")
            return

        w_id, w_name, w_email, w_phone = 6, 22, 28, 16
        sep_line = f"+{'-' * (w_id + 2)}+{'-' * (w_name + 2)}+{'-' * (w_email + 2)}+{'-' * (w_phone + 2)}+"

        print("\n" + sep_line)
        print(
            f"| {Color.BOLD}{'ID':<{w_id}}{Color.RESET} "
            f"| {Color.BOLD}{'Name':<{w_name}}{Color.RESET} "
            f"| {Color.BOLD}{'Email':<{w_email}}{Color.RESET} "
            f"| {Color.BOLD}{'Phone':<{w_phone}}{Color.RESET} |"
        )
        print(sep_line)
        for c in contacts:
            c_id = str(c.id)
            print(
                f"| {c_id:<{w_id}} "
                f"| {truncate(c.name, w_name):<{w_name}} "
                f"| {truncate(c.email, w_email):<{w_email}} "
                f"| {truncate(c.phone, w_phone):<{w_phone}} |"
            )
        print(sep_line)
        print(f"{Color.CYAN}Total displayed: {len(contacts)} contact(s){Color.RESET}\n")

    def print_contact_card(self, c: Contact):
        width = 64
        sep = f"+{'-' * width}+"
        mid_sep = f"+{'-' * 14}+{'-' * (width - 15)}+"
        title = f" Contact #{c.id} Details "

        print(f"\n{Color.CYAN}{sep}{Color.RESET}")
        print(f"{Color.CYAN}|{Color.BOLD}{title.center(width)}{Color.RESET}{Color.CYAN}|{Color.RESET}")
        print(f"{Color.CYAN}{mid_sep}{Color.RESET}")
        fields = [
            ("ID", str(c.id)),
            ("Name", c.name),
            ("Email", c.email),
            ("Phone", c.phone),
            ("Address", c.address or "(None)"),
            ("Created At", c.created_at or "-"),
            ("Updated At", c.updated_at or "-"),
        ]
        for label, val in fields:
            print(
                f"| {Color.BOLD}{label:<12}{Color.RESET}"
                f"| {val:<{width - 17}} |"
            )
        print(f"{Color.CYAN}{mid_sep}{Color.RESET}\n")

    # ------------------------------------------------------------- ACTIONS
    def create_contact(self):
        print(f"\n{Color.BOLD}--- Create New Contact ---{Color.RESET}")
        print(f"{Color.DIM}Type 'cancel' at any prompt to return to main menu.{Color.RESET}\n")

        name = self.prompt_field("Name", validate_name)
        email = self.prompt_field("Email", validate_email)
        phone = self.prompt_field("Phone", validate_phone)
        address = self.prompt_field("Address", validate_address, optional=True)

        contact = Contact(name=name, email=email, phone=phone, address=address)
        saved = self.repo.create(contact)
        print(f"\n{success(f'Contact successfully created with ID {highlight(str(saved.id))}!')}")
        self.print_contact_card(saved)

    def list_contacts(self):
        print(f"\n{Color.BOLD}--- All Contacts ---{Color.RESET}")
        total = self.repo.count()
        if total == 0:
            print(f"\n{info('Your contact book is currently empty. Use option 1 or 9 to add contacts.')}\n")
            return

        print("Sort order:")
        print("  1. Name (A to Z) [Default]")
        print("  2. ID (Ascending)")
        print("  3. Recently Added (Newest First)")
        sort_choice = input(f"{Color.BOLD}Select sort [1-3, default 1]: {Color.RESET}").strip()

        if sort_choice == "2":
            contacts = self.repo.get_all(sort_by="id", order="asc")
        elif sort_choice == "3":
            contacts = self.repo.get_all(sort_by="id", order="desc")
        else:
            contacts = self.repo.get_all(sort_by="name", order="asc")

        self.print_table(contacts)

    def view_contact(self):
        print(f"\n{Color.BOLD}--- View Contact Details ---{Color.RESET}")
        contact_id = self.prompt_field("Enter Contact ID", lambda val: validate_non_empty_int(val, "Contact ID"))
        contact = self.repo.get_by_id(contact_id)
        self.print_contact_card(contact)

    def update_contact(self):
        print(f"\n{Color.BOLD}--- Update Contact ---{Color.RESET}")
        contact_id = self.prompt_field("Enter Contact ID to update", lambda val: validate_non_empty_int(val, "Contact ID"))
        existing = self.repo.get_by_id(contact_id)
        self.print_contact_card(existing)

        print(f"{Color.DIM}Press [Enter] to keep current value, or type new value.{Color.RESET}\n")
        name = self.prompt_field("Name", validate_name, default=existing.name)
        email = self.prompt_field("Email", validate_email, default=existing.email)
        phone = self.prompt_field("Phone", validate_phone, default=existing.phone)
        address = self.prompt_field("Address", validate_address, optional=True, default=existing.address)

        updated = Contact(name=name, email=email, phone=phone, address=address)
        result = self.repo.update(contact_id, updated)
        print(f"\n{success(f'Contact #{result.id} updated successfully!')}")
        self.print_contact_card(result)

    def delete_contact(self):
        print(f"\n{Color.BOLD}--- Delete Contact ---{Color.RESET}")
        contact_id = self.prompt_field("Enter Contact ID to delete", lambda val: validate_non_empty_int(val, "Contact ID"))
        existing = self.repo.get_by_id(contact_id)
        self.print_contact_card(existing)

        confirm = input(f"{Color.RED}{Color.BOLD}Are you sure you want to delete this contact? Type 'yes' to confirm: {Color.RESET}").strip().lower()
        if confirm == "yes":
            self.repo.delete(contact_id)
            print(f"\n{success(f'Contact #{contact_id} ({existing.name}) deleted successfully.')}\n")
        else:
            print(f"\n{info('Deletion cancelled.')}\n")

    def search_contacts(self):
        print(f"\n{Color.BOLD}--- Search Contacts ---{Color.RESET}")
        keyword = input(f"{Color.BOLD}Enter name, email, or phone keyword: {Color.RESET}").strip()
        if not keyword:
            raise ValidationError("Search keyword cannot be empty.")

        results = self.repo.search(keyword)
        if not results:
            print(f"\n{info(f'No matching contacts found for \"{keyword}\".')}\n")
        else:
            print(f"\n{success(f'Found {len(results)} matching contact(s):')}")
            self.print_table(results)

    def export_contacts(self):
        print(f"\n{Color.BOLD}--- Export Contacts ---{Color.RESET}")
        if self.repo.count() == 0:
            print(f"\n{info('No contacts available to export.')}\n")
            return

        print("Export formats:")
        print("  1. CSV format (.csv)")
        print("  2. JSON format (.json)")
        fmt = input(f"{Color.BOLD}Select format [1-2, default 1]: {Color.RESET}").strip()

        data_dir = Path(self.repo.db.db_path).parent
        if fmt == "2":
            filepath = data_dir / "contacts_export.json"
            count = self.repo.export_to_json(str(filepath))
            print(f"\n{success(f'Successfully exported {count} contacts to JSON:')}")
            print(f"  {highlight(str(filepath))}\n")
        else:
            filepath = data_dir / "contacts_export.csv"
            count = self.repo.export_to_csv(str(filepath))
            print(f"\n{success(f'Successfully exported {count} contacts to CSV:')}")
            print(f"  {highlight(str(filepath))}\n")

    def import_contacts(self):
        print(f"\n{Color.BOLD}--- Import Contacts from CSV ---{Color.RESET}")
        default_path = Path(self.repo.db.db_path).parent / "contacts_export.csv"
        path_in = input(f"{Color.BOLD}Enter CSV file path [{default_path}]: {Color.RESET}").strip()
        target = path_in if path_in else str(default_path)

        res = self.repo.import_from_csv(target)
        imp = res["imported"]
        skp = res["skipped"]
        print(f"\n{success(f'Import completed: {imp} contacts imported, {skp} skipped (duplicates/invalid).')}\n")

    def seed_sample_data(self):
        print(f"\n{Color.BOLD}--- Populate Sample Demo Contacts ---{Color.RESET}")
        added = self.repo.seed_sample_data()
        if added > 0:
            print(f"\n{success(f'Added {added} realistic demo contacts to your database!')}\n")
        self.print_table(self.repo.get_all())

    def show_statistics(self):
        print(f"\n{Color.BOLD}--- Database Summary & Statistics ---{Color.RESET}")
        stats = self.repo.get_statistics()
        total = stats["total"]
        db_path = str(self.repo.db.db_path)

        width = 60
        sep = f"+{'-' * width}+"
        mid_sep = f"+{'-' * 30}+{'-' * (width - 31)}+"

        print(f"\n{Color.CYAN}{sep}{Color.RESET}")
        print(f"{Color.CYAN}|{Color.BOLD}{'CONTACT MANAGER METRICS'.center(width)}{Color.RESET}{Color.CYAN}|{Color.RESET}")
        print(f"{Color.CYAN}{mid_sep}{Color.RESET}")
        print(f"| {Color.BOLD}{'Total Contacts':<28}{Color.RESET}| {str(total):<{width - 33}} |")
        print(f"| {Color.BOLD}{'Database File':<28}{Color.RESET}| {truncate(Path(db_path).name, width - 35):<{width - 33}} |")
        if stats["newest"]:
            print(f"| {Color.BOLD}{'Newest Contact':<28}{Color.RESET}| {truncate(stats['newest'].name, width - 35):<{width - 33}} |")
        if stats["oldest"]:
            print(f"| {Color.BOLD}{'Oldest Contact':<28}{Color.RESET}| {truncate(stats['oldest'].name, width - 35):<{width - 33}} |")
        print(f"{Color.CYAN}{sep}{Color.RESET}\n")

    def clear_database(self):
        print(f"\n{Color.RED}{Color.BOLD}--- RESET DATABASE (CLEAR ALL CONTACTS) ---{Color.RESET}")
        total = self.repo.count()
        if total == 0:
            print(f"\n{info('Database is already empty.')}\n")
            return

        print(f"{warning(f'WARNING: This will permanently delete all {total} contact(s)!')}")
        confirm = input(f"{Color.RED}{Color.BOLD}Type 'RESET' in uppercase to confirm: {Color.RESET}").strip()
        if confirm == "RESET":
            deleted = self.repo.clear_all()
            print(f"\n{success(f'Database reset complete. {deleted} contact(s) deleted.')}\n")
        else:
            print(f"\n{info('Reset aborted. Your data was not touched.')}\n")

    def launch_gui(self):
        print(f"\n{info('Opening NexusContact Web GUI at http://localhost:5000 in your browser...')}")
        import subprocess
        import webbrowser
        try:
            webbrowser.open("http://localhost:5000")
            print(f"{success('Browser launched! (If web server is not running, run python web_app.py or run_gui.bat)')}\n")
        except Exception as exc:
            print(f"{error(f'Could not launch browser: {exc}')}\n")
