"""
utils.py
Reusable validation and helper functions used across the application.
Keeping validation logic here (separate from CLI and DB code) keeps the
codebase modular and each function independently testable.
"""

import os
import re
import sys
from datetime import datetime

from src.exceptions import ValidationError

NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s'.-]{1,49}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9\s-]{7,15}$")


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def init_terminal():
    """Enable ANSI escape sequence processing and UTF-8 encoding on Windows terminals."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if os.name == "nt":
        os.system("")


def success(text: str) -> str:
    return f"{Color.GREEN}{Color.BOLD}[OK] {text}{Color.RESET}"


def error(text: str) -> str:
    return f"{Color.RED}{Color.BOLD}[X] {text}{Color.RESET}"


def warning(text: str) -> str:
    return f"{Color.YELLOW}{Color.BOLD}[!] {text}{Color.RESET}"


def info(text: str) -> str:
    return f"{Color.CYAN}{Color.BOLD}[i] {text}{Color.RESET}"


def highlight(text: str) -> str:
    return f"{Color.BOLD}{Color.CYAN}{text}{Color.RESET}"


def validate_name(name: str) -> str:
    """Validate a contact's name. Returns the cleaned name or raises ValidationError."""
    if name is None:
        raise ValidationError("Name cannot be empty.")
    name = name.strip()
    if not name:
        raise ValidationError("Name cannot be empty.")
    if not NAME_PATTERN.match(name):
        raise ValidationError(
            "Name must be 2-50 characters and contain only letters, spaces, "
            "apostrophes, periods or hyphens."
        )
    return name


def validate_email(email: str) -> str:
    """Validate an email address. Returns the cleaned email or raises ValidationError."""
    if email is None:
        raise ValidationError("Email cannot be empty.")
    email = email.strip().lower()
    if not email:
        raise ValidationError("Email cannot be empty.")
    if not EMAIL_PATTERN.match(email):
        raise ValidationError(f"'{email}' is not a valid email address.")
    return email


def validate_phone(phone: str) -> str:
    """Validate a phone number. Returns the cleaned phone number or raises ValidationError."""
    if phone is None:
        raise ValidationError("Phone number cannot be empty.")
    phone = phone.strip()
    if not phone:
        raise ValidationError("Phone number cannot be empty.")
    if not PHONE_PATTERN.match(phone):
        raise ValidationError(
            "Phone number must be 7-15 digits, and may include spaces, "
            "hyphens, or a leading '+'."
        )
    return phone


def validate_address(address: str) -> str:
    """Validate (lightly) and clean an address field. Address is optional."""
    if address is None:
        return ""
    address = address.strip()
    if len(address) > 200:
        raise ValidationError("Address must be under 200 characters.")
    return address


def validate_non_empty_int(value: str, field_name: str = "ID") -> int:
    """Validate that a string represents a positive integer (e.g. a record ID)."""
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_name} cannot be empty.")
    try:
        result = int(str(value).strip())
    except ValueError:
        raise ValidationError(f"{field_name} must be a whole number.")
    if result <= 0:
        raise ValidationError(f"{field_name} must be a positive number.")
    return result


def current_timestamp() -> str:
    """Return the current timestamp formatted for storage/display."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def truncate(text: str, length: int = 30) -> str:
    """Truncate text for clean table display, adding ellipsis if needed."""
    text = text or ""
    return text if len(text) <= length else text[: length - 3] + "..."

