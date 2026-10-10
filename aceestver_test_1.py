# ==============================================================================
# REQUIREMENTS:
#   pip install pytest matplotlib
#
# LOCAL EXECUTION:
#   pytest aceestver_test_1.py -v
#
# HEADLESS RUN (Docker / Linux EC2 / CI):
#   xvfb-run -a pytest aceestver_test_1.py -v
# ==============================================================================

import tkinter as tk
from unittest.mock import MagicMock, patch
import pytest

from aceestver_gymapp import ACEestApp


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    """Initializes the application using an isolated temporary SQLite database."""
    test_db = str(tmp_path / "test_fitness.db")
    monkeypatch.setattr("aceestver_gymapp.DB_NAME", test_db)

    root = tk.Tk()
    app = ACEestApp(root)
    yield app

    try:
        app.conn.close()
    except Exception:
        pass
    root.destroy()


# ==============================================================================
# 1. INITIALIZATION & SCHEMA TESTS
# ==============================================================================


def test_initial_state_and_defaults(app_instance):
    """Verify default values on UI startup."""
    assert app_instance.name.get() == ""
    assert app_instance.age.get() == 0
    assert app_instance.weight.get() == 0.0
    assert app_instance.program.get() == ""
    assert app_instance.adherence.get() == 0


def test_database_tables_exist(app_instance):
    """Verify that both clients and progress tables are created."""
    app_instance.cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('clients', 'progress')"
    )
    tables = [row[0] for row in app_instance.cur.fetchall()]
    assert "clients" in tables
    assert "progress" in tables


# ==============================================================================
# 2. SAVE CLIENT TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_validation_missing_name(mock_err, app_instance):
    """Ensure error is displayed and DB is untouched when name is empty."""
    app_instance.name.set("")
    app_instance.program.set("Fat Loss (FL)")
    app_instance.save_client()

    mock_err.assert_called_once_with("Error", "Name and Program required")
    app_instance.cur.execute("SELECT COUNT(*) FROM clients")
    assert app_instance.cur.fetchone()[0] == 0


@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_validation_missing_program(mock_err, app_instance):
    """Ensure error is displayed when program is empty."""
    app_instance.name.set("John")
    app_instance.program.set("")
    app_instance.save_client()

    mock_err.assert_called_once_with("Error", "Name and Program required")


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
    """Verify client insertion and calorie multiplier calculation."""
    app_instance.name.set("Jane")
    app_instance.age.set(28)
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
    assert row[0] == 28
    assert row[1] == weight
    assert row[2] == program_name
    assert row[3] == expected_calories


@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_db_exception(mock_err, app_instance):
    """Verify DB exception handling block during save."""
    app_instance.name.set("CrashTest")
    app_instance.program.set("Beginner (BG)")

    # Replace cursor object directly with a mock to avoid read-only attribute errors
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("Disk failure")
    app_instance.cur = mock_cursor

    app_instance.save_client()

    mock_err.assert_called_once_with("DB Error", "Disk failure")


# ==============================================================================
# 3. LOAD CLIENT TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showwarning")
def test_load_client_not_found(mock_warn, app_instance):
    """Verify warning when querying a non-existent client."""
    app_instance.name.set("NonExistent")
    app_instance.load_client()

    mock_warn.assert_called_once_with("Not Found", "Client not found")


def test_load_client_success(app_instance):
    """Verify loading populates fields and summary block."""
    app_instance.cur.execute(
        """
        INSERT INTO clients (name, age, weight, program, calories)
        VALUES (?, ?, ?, ?, ?)
    """,
        ("Alice", 29, 64.0, "Muscle Gain (MG)", 2240),
    )
    app_instance.conn.commit()

    app_instance.name.set("Alice")
    app_instance.load_client()

    assert app_instance.age.get() == 29
    assert app_instance.weight.get() == 64.0
    assert app_instance.program.get() == "Muscle Gain (MG)"

    summary = app_instance.summary.get("1.0", "end")
    assert "Alice" in summary
    assert "64.0 kg" in summary
    assert "2240 kcal/day" in summary


# ==============================================================================
# 4. PROGRESS LOGGING TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_progress_success(mock_info, app_instance):
    """Verify progress record is inserted with formatted calendar week."""
    app_instance.name.set("Alice")
    app_instance.adherence.set(85)

    app_instance.save_progress()

    mock_info.assert_called_once_with("Progress Saved", "Weekly progress logged")

    app_instance.cur.execute(
        "SELECT client_name, week, adherence FROM progress WHERE client_name=?",
        ("Alice",),
    )
    row = app_instance.cur.fetchone()
    assert row is not None
    assert row[0] == "Alice"
    assert "Week" in row[1]
    assert row[2] == 85


# ==============================================================================
# 5. PROGRESS CHART TESTS
# ==============================================================================


@patch("aceestver_gymapp.messagebox.showwarning")
def test_show_progress_chart_missing_name(mock_warn, app_instance):
    """Verify warning when attempting to view chart with no client name."""
    app_instance.name.set("")
    app_instance.show_progress_chart()

    mock_warn.assert_called_once_with("No Client", "Enter client name first")


@patch("aceestver_gymapp.messagebox.showinfo")
def test_show_progress_chart_no_data(mock_info, app_instance):
    """Verify informational dialog when client exists but has no logged progress."""
    app_instance.name.set("NewUser")
    app_instance.show_progress_chart()

    mock_info.assert_called_once_with(
        "No Data", "No progress data available for this client"
    )


@patch("aceestver_gymapp.plt.show")
@patch("aceestver_gymapp.plt.plot")
def test_show_progress_chart_success(mock_plot, mock_show, app_instance):
    """Verify matplotlib plot generation when progress data exists."""
    # Clear residual records created in prior tests
    app_instance.cur.execute("DELETE FROM progress")
    app_instance.conn.commit()

    app_instance.cur.executemany(
        """
        INSERT INTO progress (client_name, week, adherence)
        VALUES (?, ?, ?)
    """,
        [
            ("Alice", "Week 01 - 2026", 75),
            ("Alice", "Week 02 - 2026", 90),
        ],
    )
    app_instance.conn.commit()

    app_instance.name.set("Alice")
    app_instance.show_progress_chart()

    # Verify plt.plot was called with the correct extracted series
    mock_plot.assert_called_once()
    weeks_arg, adherence_arg = mock_plot.call_args[0][:2]
    assert weeks_arg == ["Week 01 - 2026", "Week 02 - 2026"]
    assert adherence_arg == [75, 90]

    # Verify plt.show was triggered
    mock_show.assert_called_once()