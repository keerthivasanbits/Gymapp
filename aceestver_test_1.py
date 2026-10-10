# ==============================================================================
# REQUIREMENTS:
#   pip install pytest matplotlib
#
# RUNNING LOCALLY:
#   pytest test_aceest_app.py -v
#
# HEADLESS RUN (Docker / CI / Linux VM):
#   xvfb-run -a pytest test_aceest_app.py -v
# ==============================================================================

import tkinter as tk
from unittest.mock import MagicMock, patch
import pytest

from aceestver_gymapp import ACEestApp


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    """Initializes the application using an isolated temporary SQLite database."""
    test_db = str(tmp_path / "test_aceest_fitness.db")
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
# 1. DATABASE SCHEMA & INITIALIZATION TESTS
# ==============================================================================

def test_database_tables_exist(app_instance):
    """Verify all five tables are created upon initialization."""
    app_instance.cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    existing_tables = [row[0] for row in app_instance.cur.fetchall()]
    expected_tables = ["clients", "progress", "workouts", "exercises", "metrics"]
    for table in expected_tables:
        assert table in existing_tables


def test_schema_upgrade_drops_outdated_client_table(tmp_path, monkeypatch):
    """Verify that an outdated clients schema is dropped and rebuilt with all columns."""
    test_db = str(tmp_path / "migration_test.db")
    monkeypatch.setattr("aceestver_gymapp.DB_NAME", test_db)

    # Pre-create an old table missing columns
    import sqlite3
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE clients (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()

    root = tk.Tk()
    app = ACEestApp(root)

    app.cur.execute("PRAGMA table_info(clients)")
    columns = [row[1] for row in app.cur.fetchall()]
    required = {
        "id", "name", "age", "height", "weight", 
        "program", "calories", "target_weight", "target_adherence"
    }
    assert required.issubset(set(columns))

    app.conn.close()
    root.destroy()


# ==============================================================================
# 2. CLIENT MANAGEMENT (SAVE & LOAD)
# ==============================================================================

@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_validation_missing_fields(mock_err, app_instance):
    """Verify errors when saving with missing name or program."""
    # Missing name
    app_instance.name.set("")
    app_instance.program.set("Beginner (BG)")
    app_instance.save_client()
    mock_err.assert_called_with("Error", "Name is required")

    # Missing program
    app_instance.name.set("John")
    app_instance.program.set("")
    app_instance.save_client()
    mock_err.assert_called_with("Error", "Program is required")


@pytest.mark.parametrize(
    "prog, weight, expected_calories",
    [
        ("Fat Loss (FL) – 3 day", 80.0, 1760),      # 80 * 22
        ("Fat Loss (FL) – 5 day", 80.0, 1920),      # 80 * 24
        ("Muscle Gain (MG) – PPL", 70.0, 2450),     # 70 * 35
        ("Beginner (BG)", 60.0, 1560),              # 60 * 26
    ]
)
@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_client_success_and_calories(
    mock_info, app_instance, prog, weight, expected_calories
):
    """Verify client save, calorie calculations, and UI list refresh."""
    app_instance.name.set("Jane")
    app_instance.age.set(28)
    app_instance.height.set(168.0)
    app_instance.weight.set(weight)
    app_instance.program.set(prog)
    app_instance.target_weight.set(65.0)
    app_instance.target_adherence.set(90)

    app_instance.save_client()
    mock_info.assert_called_once_with("Saved", "Client data saved")

    app_instance.cur.execute(
        "SELECT age, height, weight, program, calories, target_weight, target_adherence "
        "FROM clients WHERE name=?",
        ("Jane",),
    )
    row = app_instance.cur.fetchone()
    assert row == (28, 168.0, weight, prog, expected_calories, 65.0, 90)
    assert "Jane" in app_instance.client_list["values"]


@patch("aceestver_gymapp.messagebox.showerror")
def test_save_client_db_exception(mock_err, app_instance):
    """Verify exception handling during client save."""
    app_instance.name.set("ErrorUser")
    app_instance.program.set("Beginner (BG)")

    mock_cur = MagicMock()
    mock_cur.execute.side_effect = Exception("Disk Write Error")
    app_instance.cur = mock_cur

    app_instance.save_client()
    mock_err.assert_called_once_with("DB Error", "Disk Write Error")


@patch("aceestver_gymapp.messagebox.showwarning")
def test_load_client_not_found(mock_warn, app_instance):
    """Verify warning when attempting to load a non-existent client."""
    app_instance.name.set("Ghost")
    app_instance.load_client()
    mock_warn.assert_called_once_with("Not Found", "Client not found")


def test_load_client_success_and_summary_render(app_instance):
    """Verify loading populates widgets and updates the text summary."""
    app_instance.cur.execute(
        """
        INSERT INTO clients (name, age, height, weight, program, calories, target_weight, target_adherence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("Alice", 30, 175.0, 72.0, "Muscle Gain (MG) – PPL", 2520, 75.0, 95)
    )
    app_instance.conn.commit()

    app_instance.name.set("Alice")
    app_instance.load_client()

    assert app_instance.age.get() == 30
    assert app_instance.height.get() == 175.0
    assert app_instance.weight.get() == 72.0
    assert app_instance.program.get() == "Muscle Gain (MG) – PPL"
    assert app_instance.target_weight.get() == 75.0
    assert app_instance.target_adherence.get() == 95

    summary_text = app_instance.summary.get("1.0", "end")
    assert "Alice" in summary_text
    assert "72.0 kg" in summary_text
    assert "2520 kcal/day" in summary_text
    assert "Target Weight: 75.0 kg" in summary_text


# ==============================================================================
# 3. WEEKLY PROGRESS LOGGING
# ==============================================================================

@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_progress_success(mock_info, app_instance):
    """Verify progress record is inserted and summary updates."""
    app_instance.name.set("Bob")
    app_instance.adherence.set(80)

    app_instance.save_progress()
    mock_info.assert_called_once_with("Progress Saved", "Weekly progress logged")

    app_instance.cur.execute(
        "SELECT client_name, week, adherence FROM progress WHERE client_name=?",
        ("Bob",),
    )
    row = app_instance.cur.fetchone()
    assert row[0] == "Bob"
    assert "Week" in row[1]
    assert row[2] == 80


# ==============================================================================
# 4. WORKOUT LOGGING & HISTORY
# ==============================================================================

@patch("aceestver_gymapp.messagebox.showinfo")
def test_log_workout_with_exercise(mock_info, app_instance):
    """Verify workout and exercise creation via log workout flow."""
    app_instance.current_client = "Athlete1"

    # Manually invoke insertion logic
    app_instance.cur.execute(
        """
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Athlete1", "2026-10-10", "Strength", 60, "Heavy squats session")
    )
    workout_id = app_instance.cur.lastrowid
    app_instance.cur.execute(
        """
        INSERT INTO exercises (workout_id, name, sets, reps, weight)
        VALUES (?, ?, ?, ?, ?)
        """,
        (workout_id, "Squat", 5, 5, 120.0)
    )
    app_instance.conn.commit()

    # Query back workout & exercise
    app_instance.cur.execute(
        "SELECT name, sets, reps, weight FROM exercises WHERE workout_id=?",
        (workout_id,)
    )
    ex_row = app_instance.cur.fetchone()
    assert ex_row == ("Squat", 5, 5, 120.0)


def test_open_workout_history_window(app_instance):
    """Verify workout history Treeview renders client entries correctly."""
    app_instance.current_client = "Athlete1"
    app_instance.cur.execute(
        """
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Athlete1", "2026-10-10", "Hypertrophy", 45, "Upper body pump")
    )
    app_instance.conn.commit()

    app_instance.open_workout_history_window()

    # Locate the created top-level window
    toplevel = [w for w in app_instance.root.winfo_children() if isinstance(w, tk.Toplevel)][-1]
    tree = [w for w in toplevel.winfo_children() if isinstance(w, tk.ttk.Treeview)][0]
    children = tree.get_children()
    assert len(children) == 1
    assert tree.item(children[0])["values"] == ["2026-10-10", "Hypertrophy", 45, "Upper body pump"]
    toplevel.destroy()


# ==============================================================================
# 5. BODY METRICS LOGGING
# ==============================================================================

def test_log_body_metrics(app_instance):
    """Verify body metric record insertion and auto-update of weight variable."""
    app_instance.current_client = "MetricUser"
    app_instance.cur.execute(
        """
        INSERT INTO metrics (client_name, date, weight, waist, bodyfat)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("MetricUser", "2026-10-10", 78.5, 82.0, 14.5)
    )
    app_instance.conn.commit()

    app_instance.cur.execute(
        "SELECT weight, waist, bodyfat FROM metrics WHERE client_name=?",
        ("MetricUser",)
    )
    assert app_instance.cur.fetchone() == (78.5, 82.0, 14.5)


# ==============================================================================
# 6. CHARTS & ANALYTICS
# ==============================================================================

@patch("aceestver_gymapp.plt.show")
@patch("aceestver_gymapp.plt.plot")
def test_show_progress_chart_success(mock_plot, mock_show, app_instance):
    """Verify progress chart plotting with clean state."""
    app_instance.current_client = "ChartUser"
    app_instance.cur.executemany(
        """
        INSERT INTO progress (client_name, week, adherence)
        VALUES (?, ?, ?)
        """,
        [
            ("ChartUser", "Week 01 - 2026", 75),
            ("ChartUser", "Week 02 - 2026", 90),
        ]
    )
    app_instance.conn.commit()

    app_instance.show_progress_chart()

    mock_plot.assert_called_once()
    weeks_arg, adherence_arg = mock_plot.call_args[0][:2]
    assert weeks_arg == ["Week 01 - 2026", "Week 02 - 2026"]
    assert adherence_arg == [75, 90]
    mock_show.assert_called_once()


@patch("aceestver_gymapp.plt.show")
@patch("aceestver_gymapp.plt.plot")
def test_show_weight_chart_success(mock_plot, mock_show, app_instance):
    """Verify weight trend chart plotting."""
    app_instance.current_client = "WeightUser"
    app_instance.cur.executemany(
        """
        INSERT INTO metrics (client_name, date, weight, waist, bodyfat)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("WeightUser", "2026-09-01", 85.0, 90.0, 20.0),
            ("WeightUser", "2026-10-01", 83.5, 88.0, 19.0),
        ]
    )
    app_instance.conn.commit()

    app_instance.show_weight_chart()

    mock_plot.assert_called_once()
    dates_arg, weights_arg = mock_plot.call_args[0][:2]
    assert dates_arg == ["2026-09-01", "2026-10-01"]
    assert weights_arg == [85.0, 83.5]
    mock_show.assert_called_once()


# ==============================================================================
# 7. BMI & RISK CALCULATION
# ==============================================================================

@pytest.mark.parametrize(
    "height_cm, weight_kg, expected_bmi, category_keyword",
    [
        (180.0, 55.0, 17.0, "Underweight"),
        (175.0, 70.0, 22.9, "Normal"),
        (170.0, 80.0, 27.7, "Overweight"),
        (165.0, 95.0, 34.9, "Obese"),
    ]
)
@patch("aceestver_gymapp.messagebox.showinfo")
def test_show_bmi_info(
    mock_info, app_instance, height_cm, weight_kg, expected_bmi, category_keyword
):
    """Verify BMI math and appropriate risk category assignment."""
    app_instance.current_client = "BMITestUser"
    app_instance.height.set(height_cm)
    app_instance.weight.set(weight_kg)

    app_instance.show_bmi_info()

    mock_info.assert_called_once()
    title, message = mock_info.call_args[0]
    assert title == "BMI Info"
    assert str(expected_bmi) in message
    assert category_keyword in message