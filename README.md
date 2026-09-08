# NexusContact OS • Smart Contact Manager

A modern, high-performance **CLI & Graphical Web Interface (GUI)** for managing contacts with complete **CRUD (Create, Read, Update, Delete)** operations, persistent SQLite storage, real-time search, data export/import, and beautiful cyber-glassmorphism design.

---

## 🌟 Key Features

- **Dual-Interface Architecture**:
  - **NexusContact Web GUI**: Sleek cyber-glassmorphism interface with glowing 3D nexus orb branding, live card/table view toggles, real-time search, interactive modals, and 1-click clipboard copy.
  - **NexusContact CLI**: Fast menu-driven terminal interface with ANSI color palettes, clean table alignment, and smart input validation retry loops.
- **Zero External Dependencies**: Built 100% using Python's standard library (`http.server` + `sqlite3`) and vanilla HTML5/CSS3/JavaScript. No `npm` or external pip packages required.
- **Shared SQLite Database**: Changes made in either CLI or Web GUI are instantly reflected across both interfaces.
- **Data Export / Import**: Instant CSV and formatted JSON export/import.
- **1-Click Demo Data**: Instantly seed realistic test contacts.
- **19 Unit Tests**: Comprehensive test suite covering validation, CRUD, sorting, and export/import.

---

## 🚀 Quick Start

### 1. Launch the Web GUI (Browser Dashboard):
```bash
python web_app.py
```
Or double-click:
```cmd
run_gui.bat
```
Then visit **`http://localhost:5000`** in your browser.

### 2. Launch the CLI Tool:
```bash
python main.py
```
Or double-click:
```cmd
run.bat
```

### 3. Run All Automated Unit Tests:
```bash
python -m unittest discover -s cli-crud-app/tests -v
```

---

## 📁 Project Structure

```
cli-crud-app/
├── main.py                 # Root CLI entry point
├── web_app.py              # Zero-dependency Web GUI server & REST API
├── run.bat                 # Windows 1-click CLI launcher
├── run_gui.bat             # Windows 1-click Web GUI launcher
├── requirements.txt         # Standard library only (no pip install needed)
├── README.md               # Root documentation
├── web/
│   ├── index.html          # Modern glassmorphism dashboard layout
│   ├── style.css           # Electric cyan & royal indigo cyber styling
│   ├── app.js              # Client-side asynchronous controller
│   └── assets/
│       ├── logo.jpg        # 3D Nexus Orb logo
│       └── nexus_logo.jpg
├── cli-crud-app/
│   ├── data/
│   │   └── contacts.db     # SQLite database
│   ├── src/
│   │   ├── cli.py          # Interactive menu & presentation layer
│   │   ├── operations.py   # ContactRepository CRUD & business logic
│   │   ├── database.py     # SQLite connection manager & schema
│   │   ├── models.py       # Contact dataclass
│   │   ├── utils.py        # Input validation, styling & helpers
│   │   └── exceptions.py   # Custom exceptions
│   └── tests/
│       └── test_app.py     # 19 comprehensive unit tests
```

---

## 📄 License

MIT License — see [LICENSE](cli-crud-app/LICENSE) for details.
