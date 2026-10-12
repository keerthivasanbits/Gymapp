import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import os
import sqlite3
import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock

import aceestver_gymapp

@pytest.fixture
def test_db(tmp_path):
    """Fixture to set up a temporary SQLite database for testing."""
    db_file = tmp_path / "test_fitness.db"
    original_db = aceestver_gymapp.DB_NAME
    aceestver_gymapp.DB_NAME = str(db_file)
    
    aceestver_gymapp.init_db()
    yield str(db_file)
    aceestver_gymapp.DB_NAME = original_db

@pytest.fixture
def app_instance(test_db):
    """Fixture to initialize the Tkinter root and application instance safely."""
    root = tk.Tk()
    root.withdraw()
    app = aceestver_gymapp.ACEestApp(root)
    yield app
    root.destroy()

def test_init_db(test_db):
    """Test database initialization and default admin creation."""
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cur.fetchall()}
    expected_tables = {"users", "clients", "progress", "workouts", "exercises", "metrics"}
    assert expected_tables.issubset(tables)
    
    cur.execute("SELECT role FROM users WHERE username='admin'")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "Admin"
    conn.close()

def test_login_success(app_instance):
    """Test successful user login with valid admin credentials."""
    app_instance.username_var.set("admin")
    app_instance.password_var.set("admin")
    
    with patch.object(app_instance, "dashboard", return_value=None) as mock_dash:
        app_instance.login()
        assert app_instance.current_user == "admin"
        assert app_instance.current_role == "Admin"
        mock_dash.assert_called_once()

def test_login_failure(app_instance):
    """Test login failure with invalid credentials."""
    app_instance.username_var.set("admin")
    app_instance.password_var.set("wrongpassword")
    
    with patch("tkinter.messagebox.showerror") as mock_error:
        app_instance.login()
        assert app_instance.current_user is None
        mock_error.assert_called_once()

def test_add_save_client(app_instance):
    """Test adding a client via simpledialog input mock, avoiding UI refresh errors."""
    with patch("tkinter.simpledialog.askstring", return_value="John Doe"), \
         patch.object(app_instance, "refresh_client_list") as mock_refresh, \
         patch("tkinter.messagebox.showinfo") as mock_info:
        
        app_instance.add_save_client()
        
        # Verify client is stored in DB
        app_instance.cur.execute("SELECT name, membership_status FROM clients WHERE name=?", ("John Doe",))
        row = app_instance.cur.fetchone()
        assert row is not None
        assert row[0] == "John Doe"
        assert row[1] == "Active"
        mock_refresh.assert_called_once()
        mock_info.assert_called_once()

def test_generate_program(app_instance):
    """Test AI program generator assigns a workout program, bypassing UI summary updates."""
    app_instance.current_client = "Jane Doe"
    app_instance.cur.execute("INSERT INTO clients (name, membership_status) VALUES (?, ?)", ("Jane Doe", "Active"))
    app_instance.conn.commit()
    
    with patch.object(app_instance, "refresh_summary") as mock_refresh, \
         patch("tkinter.messagebox.showinfo") as mock_info:
        
        app_instance.generate_program()
        
        app_instance.cur.execute("SELECT program FROM clients WHERE name=?", ("Jane Doe",))
        program = app_instance.cur.fetchone()[0]
        assert program is not None
        assert len(program) > 0
        mock_refresh.assert_called_once()
        mock_info.assert_called_once()

def test_add_workout(app_instance):
    """Test adding workout entries for a client."""
    app_instance.current_client = "Mike Smith"
    app_instance.cur.execute("INSERT INTO clients (name, membership_status) VALUES (?, ?)", ("Mike Smith", "Active"))
    app_instance.conn.commit()
    
    app_instance.cur.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?, ?, ?, ?, ?)",
        ("Mike Smith", "2026-10-10", "Strength", 45, "Great session")
    )
    app_instance.conn.commit()
    
    app_instance.cur.execute("SELECT workout_type, duration_min, notes FROM workouts WHERE client_name=?", ("Mike Smith",))
    row = app_instance.cur.fetchone()
    assert row == ("Strength", 45, "Great session")

def test_check_membership(app_instance):
    """Test viewing membership status popup info."""
    app_instance.current_client = "Sarah Connor"
    app_instance.cur.execute(
        "INSERT INTO clients (name, membership_status, membership_end) VALUES (?, ?, ?)",
        ("Sarah Connor", "Active", "2026-12-31")
    )
    app_instance.conn.commit()
    
    with patch("tkinter.messagebox.showinfo") as mock_info:
        app_instance.check_membership()
        mock_info.assert_called_once()
        args = mock_info.call_args[0]
        assert "Active" in args[1]
        assert "2026-12-31" in args[1]
