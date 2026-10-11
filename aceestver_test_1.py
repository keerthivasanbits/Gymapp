import os
import sqlite3
import tkinter as tk
from unittest.mock import MagicMock, patch
import pytest

# Ensure no DISPLAY errors if imported outside xvfb
os.environ.setdefault("DISPLAY", ":99")

from aceestver_gymapp import ACEestApp


@pytest.fixture(autouse=True)
def mock_tkinter_dialogs():
    """Auto-mocks all Tkinter dialog popups to prevent headless test stalls."""
    with (
        patch("tkinter.messagebox.showinfo", return_value=True),
        patch("tkinter.messagebox.showwarning", return_value=True),
        patch("tkinter.messagebox.showerror", return_value=True),
        patch("tkinter.messagebox.askyesno", return_value=True),
        patch("tkinter.messagebox.askokcancel", return_value=True),
    ):
        yield


@pytest.fixture
def test_db(tmp_path):
    """Creates a temporary SQLite database for testing."""
    db_file = tmp_path / "test_gym.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    # If your app creates tables inside its own init, you can leave this minimal
    conn.commit()
    conn.close()
    return str(db_file)


@pytest.fixture
def app_instance(test_db):
    """Initializes Tkinter headlessly and executes a safe, non-blocking teardown."""
    try:
        root = tk.Tk()
        root.withdraw()  # Prevent rendering visible window
    except tk.TclError:
        pytest.skip("Tkinter display not available in current environment")

    # Flush initialization events
    root.update_idletasks()
    root.update()

    app = ACEestApp(root)
    if hasattr(app, "db_path"):
        app.db_path = test_db

    try:
        yield app
    finally:
        # 1. Cancel any pending .after() callbacks
        try:
            for after_id in root.tk.eval("after info").split():
                root.after_cancel(after_id)
        except Exception:
            pass

        # 2. Close database connection safely
        if hasattr(app, "conn") and app.conn:
            try:
                app.conn.close()
            except Exception:
                pass

        # 3. Destroy root window without blocking
        try:
            root.update_idletasks()
            root.destroy()
        except Exception:
            pass