# ==============================================================================
# REQUIREMENTS:
#   pip install pytest
#
# RUN COMMAND:
#   pytest test_aceest_sqlite.py -v
#
# HEADLESS RUN (Docker/CI/Linux Server):
#   xvfb-run -a pytest test_aceest_sqlite.py -v
# ==============================================================================

import tkinter as tk
from unittest.mock import patch
import pytest

from aceestver_gymapp import ACEestApp


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    """Initializes the Tkinter root with an isolated temporary SQLite database."""
    test_db_path = str(tmp_path / "test_aceest.db")
    monkeypatch.setattr("aceestver_gymapp.DB_NAME", test_db_path)

    root = tk.Tk()
    app = ACEestApp(root)
    yield app

    try:
        app.conn.close()
    except Exception:
        pass
    root.destroy()


# ==============================================================================
# 1. INITIALIZATION & DATABASE TESTS
# ==============================================================================


def test_initial_state_and_defaults(app_instance):
    """Verify all form input variables start with default initial values."""
    assert app_instance.name.get() == ""
    assert app_instance.age.get() == 0
    assert app_instance.weight.get() == 0.0
    assert app_instance.program.get() == ""
    assert app_instance.adherence.get() == 0


def test_database_tables_created(app_instance):
    """Verify that clients and progress tables are created in the database."""
    app_instance.cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('clients', 'progress')"
    )
    tables = [row[0] for row in app_instance.cur.fetchall()]
    assert "clients" in tables
    assert "progress" in tables


# ==============================================================================
# 2. SAVE CLIENT & VALIDATION TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_validation_missing_name(mock_error, app_instance):
    """Ensure error is displayed and DB is untouched when name is missing."""
    app_instance.name.set("")
    app_instance.program.set("Fat Loss (FL)")
    app_instance.save_client()

    mock_error.assert_called_once_with("Error", "Name and Program required")
    app_instance.cur.execute("SELECT COUNT(*) FROM clients")
    assert app_instance.cur.fetchone()[0] == 0


@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_validation_missing_program(mock_error, app_instance):
    """Ensure error is displayed and DB is untouched when program is missing."""
    app_instance.name.set("John")
    app_instance.program.set("")
    app_instance.save_client()

    mock_error.assert_called_once_with("Error", "Name and Program required")
    app_instance.cur.execute("SELECT COUNT(*) FROM clients")
    assert app_instance.cur.fetchone()[0] == 0


@pytest.mark.parametrize(
    "program_name, weight, expected_calories",
    [
        ("Fat Loss (FL)", 80.0, 1760),  # 80 * 22
        ("Muscle Gain (MG)", 70.0, 2450),  # 70 * 35
        ("Beginner (BG)", 60.0, 1560),  # 60 * 26
    ],
)
@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_client_success_and_calories(
    mock_info, app_instance, program_name, weight, expected_calories
):
    """Verify client record insertion and accurate calorie calculations."""
    app_instance.name.set("Jane")
    app_instance.age.set(27)
    app_instance.weight.set(weight)
    app_instance.program.set(program_name)

    app_instance.save_client()

    mock_info.assert_called_once_with("Saved", "Client data saved")

    app_instance.cur.execute(
        "SELECT age, weight, program, calories FROM clients WHERE name=?",
        ("Jane",),
    )
    row = app_instance.cur.fetchone()
    assert row is not None
    assert row[0] == 27
    assert row[1] == weight
    assert row[2] == program_name
    assert row[3] == expected_calories


@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_client_update_existing(mock_info, app_instance):
    """Verify INSERT OR REPLACE updates an existing client's details."""
    app_instance.name.set("John")
    app_instance.age.set(30)
    app_instance.weight.set(70.0)
    app_instance.program.set("Beginner (BG)")
    app_instance.save_client()

    # Update weight and program
    app_instance.weight.set(75.0)
    app_instance.program.set("Muscle Gain (MG)")
    app_instance.save_client()

    app_instance.cur.execute(
        "SELECT weight, program, calories FROM clients WHERE name=?", ("John",)
    )
    row = app_instance.cur.fetchone()
    assert row[0] == 75.0
    assert row[1] == "Muscle Gain (MG)"
    assert row[2] == 2625  # 75 * 35


# ==============================================================================
# 3. LOAD CLIENT TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showwarning")
def test_load_client_not_found(mock_warning, app_instance):
    """Verify warning dialog triggers when client is not found."""
    app_instance.name.set("UnknownClient")
    app_instance.load_client()

    mock_warning.assert_called_once_with("Not Found", "Client not found")


def test_load_client_success(app_instance):
    """Verify loading populates entry fields and text summary."""
    app_instance.cur.execute(
        """
        INSERT INTO clients (name, age, weight, program, calories)
        VALUES (?, ?, ?, ?, ?)
    """,
        ("Alice", 29, 65.0, "Beginner (BG)", 1690),
    )
    app_instance.conn.commit()

    app_instance.name.set("Alice")
    app_instance.load_client()

    assert app_instance.age.get() == 29
    assert app_instance.weight.get() == 65.0
    assert app_instance.program.get() == "Beginner (BG)"

    summary_text = app_instance.summary.get("1.0", "end")
    assert "Alice" in summary_text
    assert "65.0 kg" in summary_text
    assert "Beginner (BG)" in summary_text
    assert "1690 kcal/day" in summary_text


# ==============================================================================
# 4. PROGRESS LOGGING TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_progress_success(mock_info, app_instance):
    """Verify weekly progress is stored into the progress table."""
    app_instance.name.set("Alice")
    app_instance.adherence.set(90)

    app_instance.save_progress()

    mock_info.assert_called_once_with("Progress Saved", "Weekly progress logged")

    app_instance.cur.execute(
        "SELECT client_name, adherence, week FROM progress WHERE client_name=?",
        ("Alice",),
    )
    row = app_instance.cur.fetchone()
    assert row is not None
    assert row[0] == "Alice"
    assert row[1] == 90
    assert "Week" in row[2]