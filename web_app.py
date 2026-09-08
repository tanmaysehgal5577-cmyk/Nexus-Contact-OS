#!/usr/bin/env python3
"""
web_app.py
Lightweight, zero-dependency Web Application & REST API for Contact Manager.
Uses Python's standard library (http.server + sqlite3) to provide a rich graphical
interface with NexusContact OS styling.

Usage:
    python web_app.py [--port 5000] [--no-browser]
"""

import json
import mimetypes
import os
import sys
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Add cli-crud-app directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR / "cli-crud-app"
if PROJECT_DIR.exists() and str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.exceptions import (
    ContactManagerError,
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)
from src.models import Contact
from src.operations import ContactRepository
from src.utils import (
    validate_address,
    validate_email,
    validate_name,
    validate_phone,
)

WEB_DIR = BASE_DIR / "web"
DEFAULT_PORT = 5000


class NexusContactAPIHandler(SimpleHTTPRequestHandler):
    """Handles both static web assets and RESTful API endpoints."""

    def __init__(self, *args, **kwargs):
        self.repo = ContactRepository()
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _send_json(self, data, status: int = HTTPStatus.OK):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message: str, status: int = HTTPStatus.BAD_REQUEST):
        self._send_json({"error": message}, status=status)

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ------------------------------------------------------------- GET
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static assets routing
        if not path.startswith("/api/"):
            if path == "/" or not path:
                self.path = "/index.html"
            return super().do_GET()

        # API Endpoints
        try:
            if path == "/api/contacts":
                search_q = query.get("search", [""])[0].strip()
                sort_by = query.get("sort_by", ["name"])[0].strip()
                order = query.get("order", ["asc"])[0].strip()

                if search_q:
                    contacts = self.repo.search(search_q)
                else:
                    contacts = self.repo.get_all(sort_by=sort_by, order=order)

                return self._send_json({
                    "contacts": [c.to_dict() for c in contacts],
                    "total": len(contacts),
                })

            if path.startswith("/api/contacts/"):
                contact_id = int(path.split("/")[-1])
                contact = self.repo.get_by_id(contact_id)
                return self._send_json({"contact": contact.to_dict()})

            if path == "/api/stats":
                stats = self.repo.get_statistics()
                return self._send_json({
                    "total": stats["total"],
                    "newest": stats["newest"].to_dict() if stats["newest"] else None,
                    "oldest": stats["oldest"].to_dict() if stats["oldest"] else None,
                })

            if path == "/api/export":
                fmt = query.get("format", ["csv"])[0].lower()
                data_dir = Path(self.repo.db.db_path).parent
                if fmt == "json":
                    export_file = data_dir / "contacts_export.json"
                    self.repo.export_to_json(str(export_file))
                    with open(export_file, "rb") as f:
                        content = f.read()
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=contacts.json")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                else:
                    export_file = data_dir / "contacts_export.csv"
                    self.repo.export_to_csv(str(export_file))
                    with open(export_file, "rb") as f:
                        content = f.read()
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", "attachment; filename=contacts.csv")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return

            self._send_error("Endpoint not found", status=HTTPStatus.NOT_FOUND)

        except RecordNotFoundError as exc:
            self._send_error(str(exc), status=HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_error(f"Internal error: {exc}", status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # ------------------------------------------------------------- POST
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/contacts":
                data = self._read_json_body()
                name = validate_name(data.get("name", ""))
                email = validate_email(data.get("email", ""))
                phone = validate_phone(data.get("phone", ""))
                address = validate_address(data.get("address", ""))

                contact = Contact(name=name, email=email, phone=phone, address=address)
                saved = self.repo.create(contact)
                return self._send_json({"status": "ok", "contact": saved.to_dict()}, status=HTTPStatus.CREATED)

            if path == "/api/seed":
                added = self.repo.seed_sample_data()
                return self._send_json({"status": "ok", "added": added})

            if path == "/api/clear":
                deleted = self.repo.clear_all()
                return self._send_json({"status": "ok", "deleted": deleted})

            self._send_error("Endpoint not found", status=HTTPStatus.NOT_FOUND)

        except ValidationError as exc:
            self._send_error(str(exc), status=HTTPStatus.UNPROCESSABLE_ENTITY)
        except DuplicateRecordError as exc:
            self._send_error(str(exc), status=HTTPStatus.CONFLICT)
        except Exception as exc:
            self._send_error(f"Failed to process request: {exc}", status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # ------------------------------------------------------------- PUT
    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path.startswith("/api/contacts/"):
                contact_id = int(path.split("/")[-1])
                existing = self.repo.get_by_id(contact_id)
                data = self._read_json_body()

                name_raw = data.get("name")
                email_raw = data.get("email")
                phone_raw = data.get("phone")
                addr_raw = data.get("address")

                updated = Contact(
                    name=validate_name(name_raw) if name_raw else existing.name,
                    email=validate_email(email_raw) if email_raw else existing.email,
                    phone=validate_phone(phone_raw) if phone_raw else existing.phone,
                    address=validate_address(addr_raw) if addr_raw is not None else existing.address,
                )
                res = self.repo.update(contact_id, updated)
                return self._send_json({"status": "ok", "contact": res.to_dict()})

            self._send_error("Endpoint not found", status=HTTPStatus.NOT_FOUND)

        except ValidationError as exc:
            self._send_error(str(exc), status=HTTPStatus.UNPROCESSABLE_ENTITY)
        except DuplicateRecordError as exc:
            self._send_error(str(exc), status=HTTPStatus.CONFLICT)
        except RecordNotFoundError as exc:
            self._send_error(str(exc), status=HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_error(f"Update failed: {exc}", status=HTTPStatus.INTERNAL_SERVER_ERROR)

    # ------------------------------------------------------------- DELETE
    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path.startswith("/api/contacts/"):
                contact_id = int(path.split("/")[-1])
                self.repo.delete(contact_id)
                return self._send_json({"status": "ok", "deleted_id": contact_id})

            self._send_error("Endpoint not found", status=HTTPStatus.NOT_FOUND)

        except RecordNotFoundError as exc:
            self._send_error(str(exc), status=HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_error(f"Delete failed: {exc}", status=HTTPStatus.INTERNAL_SERVER_ERROR)


def run_server(port: int = DEFAULT_PORT, auto_open: bool = True):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, NexusContactAPIHandler)
    url = f"http://localhost:{port}"

    print(f"\n+======================================================================+")
    print(f"|            NEXUSCONTACT - SMART CONTACT OS GUI WEB APP               |")
    print(f"+======================================================================+")
    print(f"  Server running at: \033[96m\033[1m{url}\033[0m")
    print(f"  Press \033[93mCtrl + C\033[0m in this terminal to stop the server.\n")

    if auto_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping NexusContact Web Server... Goodbye!")
        httpd.server_close()


if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    auto_open = "--no-browser" not in sys.argv
    run_server(port=port, auto_open=auto_open)
