# NexusContact OS — Contact Manager Suite

A professional **CLI & Graphical Web Interface (GUI)** application implementing complete **CRUD (Create, Read, Update, Delete)** operations with persistent SQLite storage, input validation, data export/import, ANSI styling, and robust exception handling.

Built as **Task 1 (Week 1)** of the internship program: *"Build a CLI Application with CRUD Operations."*

---

## Features

- **Dual-Interface System**:
  - **NexusContact Web Dashboard**: Sleek cyber-glassmorphism UI with live card/table view toggles, real-time search, animated modals, and 1-click clipboard copy.
  - **Menu-Driven CLI**: Clean terminal interface with ANSI color palettes, aligned ASCII tables, and in-line validation retry loops.
- **Full CRUD**:
  - **Create**: Add new contacts with validation and instant feedback
  - **Read**: List all contacts or view details by ID in formatted cards
  - **Update**: Edit existing contacts with default-fill preservation
  - **Delete**: Remove contacts with safety confirmation
- **Multi-Order Sorting**:
  - Name (A to Z and Z to A)
  - ID (Ascending)
  - Recently Added (Newest first)
- **Fast Search** — Find contacts by name, email, or phone (case-insensitive partial match)
- **Data Export & Import**:
  - Export contacts to **CSV** (`contacts_export.csv`)
  - Export contacts to formatted **JSON** (`contacts_export.json`)
  - Import contacts from CSV with duplicate detection & validation
- **Sample Demo Data** — 1-click option to seed realistic demo contacts for testing
- **Database Metrics & Summary** — View total contacts, newest/oldest records, and database file status
- **Zero External Dependencies** — Built 100% with Python's standard library (`http.server` + `sqlite3`) and vanilla web technologies.

---

## How to Run

### 1. Web GUI Dashboard
```bash
python web_app.py
```
Or double-click `run_gui.bat`. Opens in browser at `http://localhost:5000`.

### 2. CLI Tool
```bash
python main.py
```
Or double-click `run.bat`.

---

## Running Unit Tests

```bash
python -m unittest discover -s tests -v
```
All **19 unit tests** pass with 100% success.

---

## Architecture

| Layer | File | Responsibility |
|---|---|---|
| Web GUI Frontend | `web/index.html`, `web/style.css`, `web/app.js` | Glassmorphism presentation & user interaction |
| Web API Server | `web_app.py` | Built-in HTTP REST server (`http.server`) |
| CLI Presentation | `src/cli.py` | Menus, input prompts, table formatting, and user flow |
| Business Logic | `src/operations.py` | CRUD methods, sorting, search, import/export |
| Data Model | `src/models.py` | `Contact` dataclass with dictionary/tuple conversions |
| Persistence | `src/database.py` | SQLite connection pooling context-manager & schema |
| Utilities & Styling | `src/utils.py` | Regex validators, ANSI terminal color badges, timestamping |
| Error Handling | `src/exceptions.py` | Structured hierarchy (`ValidationError`, `RecordNotFoundError`, etc.) |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
