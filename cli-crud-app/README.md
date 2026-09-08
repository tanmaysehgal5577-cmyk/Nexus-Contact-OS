# Contact Manager CLI

A professional, menu-driven Command Line Interface (CLI) application implementing complete **CRUD (Create, Read, Update, Delete)** operations with persistent SQLite storage, input validation, data export/import, ANSI styling, and robust exception handling.

Built as **Task 1 (Week 1)** of the internship program: *"Build a CLI Application with CRUD Operations."*

---

## Features

- **Menu-Driven CLI** — Simple numbered menu, no complex flags to memorize
- **Full CRUD**:
  - **Create**: Add new contacts with validation and instant feedback
  - **Read**: List all contacts or view details by ID in formatted cards
  - **Update**: Edit existing contacts with default-fill preservation
  - **Delete**: Remove contacts with safety confirmation
- **Multi-Order Sorting**:
  - Name (A to Z)
  - ID (Ascending)
  - Recently Added (Newest first)
- **Fast Search** — Find contacts by name, email, or phone (case-insensitive partial match)
- **Data Export & Import**:
  - Export contacts to **CSV** (`contacts_export.csv`)
  - Export contacts to formatted **JSON** (`contacts_export.json`)
  - Import contacts from CSV with duplicate detection & validation
- **Sample Demo Data** — 1-click option to seed realistic demo contacts for testing
- **Database Metrics & Summary** — View total contacts, newest/oldest records, and database file status
- **Smart Input Loops** — Inline retry prompts on invalid input with `cancel` support (never boots you back unexpectedly)
- **Universal Visual Aesthetics** — Clean ANSI-styled headers, status tags (`[✓]`, `[✗]`, `[!]`, `[i]`), and aligned ASCII tables
- **Zero External Dependencies** — Built 100% with Python's standard library
- **Cross-Platform & Windows-Ready** — Automatic UTF-8 console configuration and ANSI escape sequence enabling

---

## Project Structure

```
cli-crud-app/
├── main.py                 # Root launcher (runs from project root)
├── run.bat                 # Windows 1-click batch launcher
├── requirements.txt         # Standard library only (no pip install needed)
├── README.md               # Documentation
├── LICENSE                 # MIT License
├── data/
│   └── contacts.db         # SQLite database (auto-created on first run)
├── src/
│   ├── __init__.py
│   ├── cli.py              # Interactive menu & presentation layer
│   ├── operations.py       # CRUD & export/import business logic (ContactRepository)
│   ├── database.py         # SQLite connection lifecycle & schema
│   ├── models.py           # Contact data model (dataclass)
│   ├── utils.py            # Input validation, ANSI styling & helpers
│   └── exceptions.py       # Custom exception hierarchy
└── tests/
    ├── __init__.py
    └── test_app.py         # 19 comprehensive unit tests
```

---

## How to Run

### Option 1: From the Workspace Root
```bash
python main.py
```
Or on Windows:
```cmd
run.bat
```

### Option 2: From the `cli-crud-app/` Directory
```bash
cd cli-crud-app
python main.py
```

---

## Menu Options

```text
======================== MAIN MENU ======================== (Total Contacts: 1)
  1. Create a new contact
  2. List all contacts (with sort)
  3. View contact details by ID
  4. Update contact
  5. Delete contact
  6. Search contacts (Name, Email, Phone)
  7. Export contacts (CSV / JSON)
  8. Import contacts from CSV
  9. Populate sample demo contacts
  10. View database statistics & summary
  11. Clear all contacts (Reset)
  0. Exit
--------------------------------------------------------
```

---

## Running Tests

Run the complete test suite covering input validation, CRUD operations, sorting, import/export, and database resets:

```bash
python -m unittest discover -s tests -v
```

All 19 unit tests run in isolation using temporary in-memory/file databases without modifying your live contact data.

---

## Architecture

| Layer | File | Responsibility |
|---|---|---|
| Presentation | `src/cli.py` | Menus, input prompts, table formatting, and user flow |
| Business Logic | `src/operations.py` | CRUD methods, sorting, search, import/export |
| Data Model | `src/models.py` | `Contact` dataclass with dictionary/tuple conversions |
| Persistence | `src/database.py` | SQLite connection pooling context-manager & schema |
| Utilities & Styling | `src/utils.py` | Regex validators, ANSI terminal color badges, timestamping |
| Error Handling | `src/exceptions.py` | Structured hierarchy (`ValidationError`, `RecordNotFoundError`, etc.) |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
