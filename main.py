#!/usr/bin/env python3
"""
Root entry point for the Contact Manager CLI application.
Allows running the application directly from the project root:
    python main.py
"""

import sys
from pathlib import Path

# Add cli-crud-app directory to sys.path
project_root = Path(__file__).resolve().parent / "cli-crud-app"
if project_root.exists() and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli import ContactManagerCLI
from src.exceptions import DatabaseConnectionError
from src.utils import init_terminal


def main():
    init_terminal()
    if "--gui" in sys.argv:
        import web_app
        web_app.run_server()
        return

    try:
        app = ContactManagerCLI()
        app.run()
    except DatabaseConnectionError as exc:
        print(f"Fatal database error: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nApplication interrupted. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
