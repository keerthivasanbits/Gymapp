import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
import tkinter as tk

# Import your module
import app as main_module
from app import ACEestApp


@pytest.fixture
def test_db(tmp_path):
    """Creates an isolated temporary database for testing."""
    db_file = tmp_path / "test_fitness.db"
    orig_db = main_module.DB_NAME
    main_module.DB_NAME = str(db_file)
    yield str(db_file)
    main_module.DB_NAME = orig_db


@pytest.fixture
def app_instance(test_db):
    """Initializes the Tkinter root headlessly and cleans up afterward."""
    try:
        root = tk.Tk()
        root.withdraw()  # Prevent rendering visible window
    except tk.TclError:
        pytest.skip("Tkinter display not available in current environment")

    app = ACEestApp(root)
    yield app

    # Teardown: close DB connection and destroy root
    if app.conn:
        app.conn.close()
    root.destroy()


# ==========================================
# 1. DATABASE INITIALISATION TESTS
# ==========================================

def test_database_tables_created(app_instance, test_db):
    """Verify all required tables exist upon startup."""
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    expected_tables = {"clients", "progress", "workouts", "exercises", "metrics"}
    assert expected_tables.issubset(tables)


# ==========================================
# 2. CLIENT MANAGEMENT TESTS
# ==========================================

@patch("app.messagebox.showerror")
def test_save_client_validation_missing_fields(mock_showerror, app_instance):
    """Should show error when saving without required fields (name / program)."""
    app_instance.name.set("")
    app_instance.program.set("")
    app_instance.save_client()
    mock_showerror.assert_called_with("Error", "Name is required")

    app_instance.name.set("Jane Doe")
    app_instance.program.set("")
    app_instance.save_client()
    mock_showerror.assert_called_with("Error", "Program is required")


@patch("app.messagebox.showinfo")
def test_save_and_load_client_success(mock_showinfo, app_instance):
    """Test full cycle of creating a client, persisting to DB, and loading back."""
    app_instance.name.set("John Doe")
    app_instance.age.set(28)
    app_instance.height.set(178.0)
    app_instance.weight.set(75.0)
    app_instance.program.set("Fat Loss (FL) – 3 day")  # factor: 22
    app_instance.target_weight.set(70.0)
    app_instance.target_adherence.set(90)

    app_instance.save_client()
    mock_showinfo.assert_called_with("Saved", "Client data saved")

    # Clear fields to simulate a fresh state
    app_instance.age.set(0)
    app_instance.weight.set(0.0)
    app_instance.program.set("")

    # Load client back
    app_instance.name.set("John Doe")
    app_instance.load_client()

    assert app_instance.age.get() == 28
    assert app_instance.height.get() == 178.0
    assert app_instance.weight.get() == 75.0
    assert app_instance.program.get() == "Fat Loss (FL) – 3 day"
    assert app_instance.target_weight.get() == 70.0
    assert app_instance.target_adherence.get() == 90

    # Calorie calculation: weight (75) * factor (22) = 1650
    app_instance.cur.execute("SELECT calories FROM clients WHERE name=?", ("John Doe",))
    cal = app_instance.cur.fetchone()[0]
    assert cal == 1650


# ==========================================
# 3. PROGRESS LOGGING TESTS
# ==========================================

@patch("app.messagebox.showinfo")
def test_save_progress_success(mock_showinfo, app_instance):
    """Logging weekly adherence progress."""
    app_instance.name.set("Alice Smith")
    app_instance.program.set("Beginner (BG)")
    app_instance.weight.set(60.0)
    app_instance.save_client()

    app_instance.adherence.set(85)
    app_instance.save_progress()

    mock_showinfo.assert_called_with("Progress Saved", "Weekly progress logged")

    app_instance.cur.execute(
        "SELECT adherence FROM progress WHERE client_name=?", ("Alice Smith",)
    )
    result = app_instance.cur.fetchone()
    assert result is not None
    assert result[0] == 85


# ==========================================
# 4. BMI CALCULATION & RISK CHECKS
# ==========================================

@pytest.mark.parametrize(
    "height, weight, expected_category",
    [
        (180, 50, "Underweight"),   # BMI ≈ 15.4
        (180, 70, "Normal"),        # BMI ≈ 21.6
        (180, 85, "Overweight"),    # BMI ≈ 26.2
        (180, 110, "Obese"),        # BMI ≈ 34.0
    ],
)
@patch("app.messagebox.showinfo")
def test_show_bmi_info(mock_showinfo, app_instance, height, weight, expected_category):
    """Tests categorical classification of BMI formulas."""
    app_instance.current_client = "Tester"
    app_instance.height.set(height)
    app_instance.weight.set(weight)

    app_instance.show_bmi_info()

    args, _ = mock_showinfo.call_args
    assert expected_category in args[1]


# ==========================================
# 5. WORKOUT & METRIC DIALOGUE TESTS
# ==========================================

@patch("app.messagebox.showinfo")
def test_workout_logging_database_entry(mock_showinfo, app_instance):
    """Simulates workout logging and verifies relational DB record insertion."""
    app_instance.current_client = "Bob Ross"

    # Direct database insertion matching open_log_workout_window logic
    app_instance.cur.execute(
        """
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Bob Ross", "2026-10-10", "Hypertrophy", 55, "Upper body session"),
    )
    workout_id = app_instance.cur.lastrowid

    app_instance.cur.execute(
        """
        INSERT INTO exercises (workout_id, name, sets, reps, weight)
        VALUES (?, ?, ?, ?, ?)
        """,
        (workout_id, "Bench Press", 4, 8, 80.0),
    )
    app_instance.conn.commit()

    # Query back
    app_instance.cur.execute("SELECT name, sets, weight FROM exercises WHERE workout_id=?", (workout_id,))
    ex_row = app_instance.cur.fetchone()
    assert ex_row == ("Bench Press", 4, 80.0)


# ==========================================
# 6. CHART PLOTTING TESTS (MOCKED)
# ==========================================

@patch("matplotlib.pyplot.show")
def test_show_progress_chart_calls_plt(mock_plt_show, app_instance):
    """Ensures Matplotlib plot generation pipeline triggers properly without GUI blockage."""
    app_instance.current_client = "ChartUser"
    app_instance.cur.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
        ("ChartUser", "Week 40 - 2026", 80),
    )
    app_instance.conn.commit()

    app_instance.show_progress_chart()
    assert mock_plt_show.called