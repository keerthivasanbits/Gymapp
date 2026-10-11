import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock

# 1. Force headless Matplotlib before importing UI components
os.environ["MPLBACKEND"] = "Agg"
import matplotlib
matplotlib.use("Agg")

import tkinter as tk

# 2. Correct imports matching your actual filename
import aceestver_gymapp as app_module
from aceestver_gymapp import ACEestApp


@pytest.fixture
def tk_app(tmp_path, monkeypatch):
    """
    Initializes an isolated Tk instance and points DB_NAME to a clean temporary file.
    Destroys the Tk instance after the test completes.
    """
    test_db_file = str(tmp_path / "test_fitness.db")
    monkeypatch.setattr(app_module, "DB_NAME", test_db_file)

    # Initialize headless Tk instance
    root = tk.Tk()
    root.withdraw()

    # Instantiate the application
    app = ACEestApp(root)

    yield app

    # Clean up DB connection and Tkinter handles
    if app.conn:
        app.conn.close()
    root.destroy()


# =====================================================================
# Database & Authentication Tests
# =====================================================================

def test_database_initialization(tk_app):
    """Verify that all default tables and the default admin user are seeded."""
    tk_app.cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in tk_app.cur.fetchall()}
    
    expected_tables = {"users", "clients", "progress", "workouts", "exercises", "metrics"}
    assert expected_tables.issubset(tables)

    tk_app.cur.execute("SELECT username, role FROM users WHERE username='admin'")
    admin = tk_app.cur.fetchone()
    assert admin is not None
    assert admin[0] == "admin"
    assert admin[1] == "Admin"


def test_login_successful(tk_app):
    """Test login flow with valid credentials."""
    tk_app.username_var.set("admin")
    tk_app.password_var.set("admin")

    with patch.object(tk_app, "setup_ui") as mock_setup_ui:
        tk_app.login_user()
        assert tk_app.user_role == "Admin"
        assert tk_app.current_user == "admin"
        mock_setup_ui.assert_called_once()


@patch("tkinter.messagebox.showerror")
def test_login_failed(mock_error, tk_app):
    """Test login rejection on incorrect credentials."""
    tk_app.username_var.set("wrong_user")
    tk_app.password_var.set("wrong_pass")

    tk_app.login_user()

    assert tk_app.user_role is None
    mock_error.assert_called_once_with(
        "Login Failed", "Invalid credentials\nTry admin / admin"
    )


# =====================================================================
# Client Management Tests
# =====================================================================

@patch("tkinter.messagebox.showinfo")
def test_save_and_load_client(mock_info, tk_app):
    """Test saving a new client to the database and reading the values back."""
    tk_app.username_var.set("admin")
    tk_app.password_var.set("admin")
    tk_app.login_user()

    tk_app.name.set("Jane Doe")
    tk_app.age.set(28)
    tk_app.height.set(168.0)
    tk_app.weight.set(65.0)
    tk_app.program.set("Fat Loss (FL) – 3 day")
    tk_app.membership_var.set("2026-12-31")

    tk_app.save_client()
    mock_info.assert_called_with("Saved", "Client data saved")

    tk_app.cur.execute("SELECT calories, membership_expiry FROM clients WHERE name='Jane Doe'")
    row = tk_app.cur.fetchone()
    assert row is not None
    assert row[0] == int(65.0 * 22)
    assert row[1] == "2026-12-31"

    # Reset UI variables
    tk_app.name.set("")
    tk_app.age.set(0)
    tk_app.weight.set(0.0)

    # Load client back
    tk_app.current_client = "Jane Doe"
    tk_app.load_client()

    assert tk_app.name.get() == "Jane Doe"
    assert tk_app.age.get() == 28
    assert tk_app.weight.get() == 65.0


@patch("tkinter.messagebox.showerror")
def test_save_client_without_name(mock_error, tk_app):
    """Test validation preventing clients without names from being created."""
    tk_app.name.set("   ")
    tk_app.save_client()

    mock_error.assert_called_once_with("Error", "Name required")


# =====================================================================
# Program Generation Tests
# =====================================================================

@patch("tkinter.simpledialog.askstring", return_value="beginner")
@patch("tkinter.messagebox.showinfo")
def test_generate_ai_program_beginner(mock_info, mock_dialog, tk_app):
    """Test AI program generator populates TreeView rows properly for beginner."""
    tk_app.username_var.set("admin")
    tk_app.password_var.set("admin")
    tk_app.login_user()

    tk_app.cur.execute(
        "INSERT INTO clients (name, program) VALUES (?, ?)",
        ("Bob Smith", "Beginner (BG)")
    )
    tk_app.conn.commit()
    tk_app.current_client = "Bob Smith"

    tk_app.generate_ai_program()

    items = tk_app.program_tree.get_children()
    assert len(items) == 9

    row_values = tk_app.program_tree.item(items[0], "values")
    assert len(row_values) == 4
    assert row_values[0] == "Monday"
    assert int(row_values[2]) in [2, 3]
    assert int(row_values[3]) in range(8, 13)


@patch("tkinter.messagebox.showerror")
def test_generate_ai_program_no_client_selected(mock_error, tk_app):
    """Ensure error is raised if user triggers generation without selecting client."""
    tk_app.current_client = None
    tk_app.generate_ai_program()
    mock_error.assert_called_once_with("Error", "Select client first")


# =====================================================================
# PDF Export Tests
# =====================================================================

@patch("fpdf.FPDF.output")
@patch("tkinter.messagebox.showinfo")
def test_export_pdf_report(mock_info, mock_pdf_output, tk_app):
    """Test PDF generation pipeline without writing actual disk artifacts."""
    tk_app.cur.execute(
        """
        INSERT INTO clients (name, age, height, weight, program, membership_expiry)
        VALUES ('Alice Stone', 32, 175.0, 70.0, 'Muscle Gain (MG) – PPL', '2026-11-30')
        """
    )
    tk_app.conn.commit()
    tk_app.current_client = "Alice Stone"

    tk_app.export_pdf_report()

    mock_pdf_output.assert_called_once_with("Alice Stone_report.pdf")
    mock_info.assert_called_once_with(
        "PDF Exported", "Report saved as Alice Stone_report.pdf"
    )