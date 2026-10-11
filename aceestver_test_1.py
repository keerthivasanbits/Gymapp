import os
import sqlite3
import pytest
from unittest.mock import patch
import tkinter as tk

# Assuming the application file is named `aceestver_gymapp.py`
import aceestver_gymapp as app_module

TEST_DB = "test_aceest_fitness.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Isolate database execution to a temporary test DB."""
    monkeypatch.setattr(app_module, "DB_NAME", TEST_DB)
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    app_module.init_db()
    yield
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.fixture
def tk_root():
    """Initializes and tears down a Tk root instance."""
    root = tk.Tk()
    root.withdraw()  # Hide the test window
    yield root
    root.destroy()

# ==================== DATABASE TESTS ====================

def test_init_db_creates_default_admin():
    conn = sqlite3.connect(TEST_DB)
    cur = conn.cursor()
    cur.execute("SELECT username, password, role FROM users WHERE username='admin'")
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "admin"
    assert row[1] == "admin"
    assert row[2] == "Admin"

def test_init_db_schema_tables():
    conn = sqlite3.connect(TEST_DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    conn.close()

    expected_tables = {"users", "clients", "progress", "workouts", "exercises", "metrics"}
    assert expected_tables.issubset(tables)

# ==================== AUTHENTICATION TESTS ====================

def test_login_success(tk_root):
    app = app_module.ACEestApp(tk_root)
    app.username_var.set("admin")
    app.password_var.set("admin")

    with patch.object(app, "dashboard") as mock_dashboard:
        app.login()
        assert app.current_user == "admin"
        assert app.current_role == "Admin"
        mock_dashboard.assert_called_once()
    app.conn.close()

@patch("aceestver_gymapp.messagebox.showerror")
def test_login_failure_invalid_credentials(mock_error, tk_root):
    app = app_module.ACEestApp(tk_root)
    app.username_var.set("admin")
    app.password_var.set("wrong_pass")

    app.login()
    assert app.current_user is None
    assert app.current_role is None
    mock_error.assert_called_once_with("Login Failed", "Invalid credentials")
    app.conn.close()

# ==================== CLIENT MANAGEMENT TESTS ====================

@patch("aceestver_gymapp.simpledialog.askstring", return_value="John Doe")
@patch("aceestver_gymapp.messagebox.showinfo")
def test_add_save_client(mock_info, mock_dialog, tk_root):
    app = app_module.ACEestApp(tk_root)
    app.dashboard()
    app.add_save_client()

    app.cur.execute("SELECT name, membership_status FROM clients WHERE name='John Doe'")
    row = app.cur.fetchone()
    assert row is not None
    assert row[0] == "John Doe"
    assert row[1] == "Active"
    mock_info.assert_called_once()
    app.conn.close()

@patch("aceestver_gymapp.simpledialog.askstring", return_value=None)
def test_add_save_client_cancelled(mock_dialog, tk_root):
    app = app_module.ACEestApp(tk_root)
    app.dashboard()
    app.add_save_client()

    app.cur.execute("SELECT COUNT(*) FROM clients")
    count = app.cur.fetchone()[0]
    assert count == 0
    app.conn.close()

# ==================== WORKOUTS & PROGRAM TESTS ====================

@patch("aceestver_gymapp.messagebox.showwarning")
def test_generate_program_no_client_selected(mock_warn, tk_root):
    app = app_module.ACEestApp(tk_root)
    app.dashboard()
    app.current_client = None

    app.generate_program()
    mock_warn.assert_called_once_with("No Client", "Select a client first")
    app.conn.close()

@patch("aceestver_gymapp.messagebox.showinfo")
def test_generate_program_success(mock_info, tk_root):
    app = app_module.ACEestApp(tk_root)
    app.dashboard()

    # Seed client
    app.cur.execute("INSERT INTO clients (name, membership_status) VALUES ('Jane Doe', 'Active')")
    app.conn.commit()
    app.current_client = "Jane Doe"

    app.generate_program()
    app.cur.execute("SELECT program FROM clients WHERE name='Jane Doe'")
    program = app.cur.fetchone()[0]

    assert program is not None
    mock_info.assert_called_once()
    app.conn.close()

def test_add_workout_record(tk_root):
    app = app_module.ACEestApp(tk_root)
    app.dashboard()
    app.current_client = "Test Athlete"

    # Direct database insertion verification for workout logic
    app.cur.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?, ?, ?, ?, ?)",
        (app.current_client, "2026-10-12", "Strength", 45, "Leg day focus")
    )
    app.conn.commit()

    app.refresh_workouts()
    rows = app.tree_workouts.get_children()
    assert len(rows) == 1
    values = app.tree_workouts.item(rows[0])["values"]
    assert values == ["2026-10-12", "Strength", 45, "Leg day focus"]
    app.conn.close()

# ==================== REPORTING TESTS ====================

@patch("aceestver_gymapp.messagebox.showinfo")
def test_generate_pdf_success(mock_info, tk_root):
    app = app_module.ACEestApp(tk_root)
    app.dashboard()

    # Seed client with required full schema columns
    app.cur.execute("""
        INSERT INTO clients (name, age, height, weight, program, calories, target_weight, target_adherence, membership_status, membership_end)
        VALUES ('PDF User', 28, 175.0, 70.0, 'Fat Loss', 2200, 68.0, 90, 'Active', '2026-12-31')
    """)
    app.conn.commit()
    app.current_client = "PDF User"

    pdf_file = "PDF User_report.pdf"
    if os.path.exists(pdf_file):
        os.remove(pdf_file)

    app.generate_pdf()

    assert os.path.exists(pdf_file)
    assert os.path.getsize(pdf_file) > 0

    # Cleanup generated test artifact
    os.remove(pdf_file)
    app.conn.close()