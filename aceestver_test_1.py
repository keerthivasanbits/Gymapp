# ==============================================================================
# REQUIREMENTS & USAGE:
# 1. Install dependencies:
#      pip install pytest
# 2. Run locally:
#      pytest aceestver_test_1.py -v
# 3. Run headless in Docker / Linux server:
#      xvfb-run -a pytest aceestver_test_1.py -v
# ==============================================================================

import tkinter as tk
from unittest.mock import patch
import pytest

from aceestver_gymapp import ACEestApp


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    """Initializes the Tkinter root and redirects database to an isolated temporary file."""
    # Using a temporary file ensures connection persistence across operations
    # while preventing residual test data from affecting production aceest_fitness.db
    temp_db = str(tmp_path / "test_fitness.db")
    monkeypatch.setattr("aceestver_gymapp.DB_NAME", temp_db)

    root = tk.Tk()
    app = ACEestApp(root)
    yield app

    # Cleanup
    try:
        app.conn.close()
    except Exception:
        pass
    root.destroy()


# ==============================================================================
# 1. INITIALIZATION & DATABASE SCHEMA TESTS
# ==============================================================================


def test_initialization_defaults(app_instance):
    """Verify clean starting state for inputs on application startup."""
    assert app_instance.name.get() == ""
    assert app_instance.age.get() == 0
    assert app_instance.weight.get() == 0.0
    assert app_instance.program.get() == ""
    assert app_instance.adherence.get() == 0


def test_database_tables_created(app_instance):
    """Ensure the clients and progress tables are created properly."""
    app_instance.cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('clients', 'progress')"
    )
    tables = [row[0] for row in app_instance.cur.fetchall()]
    assert "clients" in tables
    assert "progress" in tables


# ==============================================================================
# 2. CLIENT MANAGEMENT TESTS (SAVE & VALIDATION)
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_validation_missing_name_or_program(
    mock_err, app_instance
):
    """Ensure an error dialog is triggered when required fields are missing."""
    app_instance.name.set("")
    app_instance.program.set("Fat Loss (FL)")
    app_instance.save_client()

    mock_err.assert_called_once_with("Error", "Name and Program required")

    # Ensure nothing was inserted into DB
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
def test_save_client_success_and_calorie_calculation(
    mock_info, app_instance, program_name, weight, expected_calories
):
    """Ensure client record and calculated calories are stored accurately."""
    app_instance.name.set("Jane Doe")
    app_instance.age.set(28)
    app_instance.weight.set(weight)
    app_instance.program.set(program_name)

    app_instance.save_client()

    mock_info.assert_called_once_with("Saved", "Client data saved")

    # Verify database contents
    app_instance.cur.execute(
        "SELECT age, weight, program, calories FROM clients WHERE name=?",
        ("Jane Doe",),
    )
    row = app_instance.cur.fetchone()
    assert row is not None
    assert row[0] == 28
    assert row[1] == weight
    assert row[2] == program_name
    assert row[3] == expected_calories


# ==============================================================================
# 3. LOAD CLIENT TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showwarning")
def test_load_client_not_found(mock_warn, app_instance):
    """Ensure a warning is displayed when loading a non-existent client."""
    app_instance.name.set("Ghost")
    app_instance.load_client()

    mock_warn.assert_called_once_with("Not Found", "Client not found")


def test_load_client_success(app_instance):
    """Verify loading populates GUI variables and the summary text view."""
    # Pre-populate client directly
    app_instance.cur.execute(
        """
        INSERT INTO clients (name, age, weight, program, calories)
        VALUES (?, ?, ?, ?, ?)
    """,
        ("Alice", 30, 65.0, "Beginner (BG)", 1690),
    )
    app_instance.conn.commit()

    # Query client via UI
    app_instance.name.set("Alice")
    app_instance.load_client()

    assert app_instance.age.get() == 30
    assert app_instance.weight.get() == 65.0
    assert app_instance.program.get() == "Beginner (BG)"

    summary_text = app_instance.summary.get("1.0", "end")
    assert "Alice" in summary_text
    assert "65.0 kg" in summary_text
    assert "1690 kcal/day" in summary_text


# ==============================================================================
# 4. PROGRESS LOGGING TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_progress_success(mock_info, app_instance):
    """Ensure weekly adherence logs are written with current calendar week."""
    app_instance.name.set("Alice")
    app_instance.adherence.set(85)

    app_instance.save_progress()

    mock_info.assert_called_once_with("Progress Saved", "Weekly progress logged")

    app_instance.cur.execute(
        "SELECT client_name, adherence, week FROM progress WHERE client_name=?",
        ("Alice",),
    )
    row = app_instance.cur.fetchone()
    assert row is not None
    assert row[0] == "Alice"
    assert row[1] == 85
    assert "Week" in row[2]