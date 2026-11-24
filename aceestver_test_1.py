import os
import sqlite3
import tkinter as tk
from unittest.mock import MagicMock, patch
import pytest

import aceestver_gymapp as app_module


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Set up an isolated test database and Tkinter app instance."""
    test_db = str(tmp_path / "test_fitness.db")
    monkeypatch.setattr(app_module, "DB_NAME", test_db)
    app_module.init_db()

    root = tk.Tk()
    root.withdraw()
    application = app_module.ACEestApp(root)

    yield application

    application.conn.close()
    root.destroy()


def login_as_admin(application):
    """Helper to log into the dashboard as default admin."""
    application.username_var.set("admin")
    application.password_var.set("admin")
    application.login()


def test_init_db(tmp_path, monkeypatch):
    """Verify all tables and default admin user are created."""
    test_db = str(tmp_path / "init_test.db")
    monkeypatch.setattr(app_module, "DB_NAME", test_db)
    app_module.init_db()

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    expected = {"users", "clients", "progress", "workouts", "exercises", "metrics"}
    assert expected.issubset(tables)

    cur.execute("SELECT username, role FROM users WHERE username='admin'")
    assert cur.fetchone() == ("admin", "Admin")
    conn.close()


def test_login_success(app):
    """Valid admin credentials should open the dashboard."""
    login_as_admin(app)
    assert app.current_user == "admin"
    assert app.current_role == "Admin"


def test_login_failure(app):
    """Invalid credentials should show an error and keep current_user None."""
    app.username_var.set("wrong_user")
    app.password_var.set("wrong_pass")

    with patch.object(app_module.messagebox, "showerror") as mock_error:
        app.login()
        mock_error.assert_called_once_with("Login Failed", "Invalid credentials")
    assert app.current_user is None


def test_add_save_client(app, monkeypatch):
    """Adding a client should insert them into the database with Active status."""
    login_as_admin(app)

    mock_simpledialog = MagicMock()
    mock_simpledialog.askstring.return_value = "John Doe"
    monkeypatch.setattr(tk, "simpledialog", mock_simpledialog, raising=False)

    with patch.object(app_module.messagebox, "showinfo") as mock_info:
        app.add_save_client()
        mock_info.assert_called_once_with("Saved", "Client John Doe saved")

    app.cur.execute("SELECT name, membership_status FROM clients WHERE name='John Doe'")
    assert app.cur.fetchone() == ("John Doe", "Active")


def test_generate_program(app):
    """Generating an AI program should save a valid program template to the DB."""
    login_as_admin(app)
    app.cur.execute(
        "INSERT INTO clients (name, membership_status) VALUES (?, ?)",
        ("Alice", "Active"),
    )
    app.conn.commit()
    app.current_client = "Alice"

    with patch.object(app_module.messagebox, "showinfo") as mock_info:
        app.generate_program()
        mock_info.assert_called_once()

    app.cur.execute("SELECT program FROM clients WHERE name='Alice'")
    program = app.cur.fetchone()[0]
    all_templates = [p for group in app.program_templates.values() for p in group]
    assert program in all_templates


def test_check_membership(app):
    """Checking membership should display the client's status and renewal date."""
    login_as_admin(app)
    app.cur.execute(
        "INSERT INTO clients (name, membership_status, membership_end) VALUES (?, ?, ?)",
        ("Bob", "Active", "2026-12-31"),
    )
    app.conn.commit()
    app.current_client = "Bob"

    with patch.object(app_module.messagebox, "showinfo") as mock_info:
        app.check_membership()
        mock_info.assert_called_once_with(
            "Membership", "Membership: Active\nRenewal Date: 2026-12-31"
        )


def test_add_workout_and_refresh(app):
    """Workouts inserted for a client should appear in the Treeview."""
    login_as_admin(app)
    app.cur.execute(
        "INSERT INTO clients (name, membership_status) VALUES (?, ?)",
        ("Charlie", "Active"),
    )
    app.cur.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?, ?, ?, ?, ?)",
        ("Charlie", "2026-11-24", "Strength", 45, "Bench press"),
    )
    app.conn.commit()
    app.current_client = "Charlie"

    app.refresh_workouts()
    items = app.tree_workouts.get_children()
    assert len(items) == 1
    values = app.tree_workouts.item(items[0], "values")
    assert values == ("2026-11-24", "Strength", "45", "Bench press")


def test_generate_pdf(app, tmp_path, monkeypatch):
    """Generating a PDF report should create the client's PDF file."""
    login_as_admin(app)
    monkeypatch.chdir(tmp_path)

    app.cur.execute(
        "INSERT INTO clients (name, age, height, weight, program, calories, membership_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Diana", 28, 165.0, 60.0, "Full Body HIIT", 2000, "Active"),
    )
    app.conn.commit()
    app.current_client = "Diana"

    with patch.object(app_module.messagebox, "showinfo") as mock_info:
        app.generate_pdf()
        mock_info.assert_called_once_with("PDF Generated", "Diana_report.pdf created")

    assert os.path.exists(tmp_path / "Diana_report.pdf")