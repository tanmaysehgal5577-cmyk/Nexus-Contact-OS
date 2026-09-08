#!/usr/bin/env python3
"""
main.py
Entry point for the Contact Manager CLI application.

Usage:
    python main.py
"""

import sys

from src.cli import ContactManagerCLI
from src.exceptions import DatabaseConnectionError
from src.utils import init_terminal


def main():
    init_terminal()
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
