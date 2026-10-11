import tkinter as tk
from unittest.mock import patch
import pytest
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
def app_instance(test_db):
    """Initializes Tkinter headlessly and executes a safe teardown."""
    try:
        root = tk.Tk()
        root.withdraw()  # Prevent rendering visible window
    except tk.TclError:
        pytest.skip("Tkinter display not available in current environment")

    # Flush pending idle events
    root.update_idletasks()
    root.update()

    app = ACEestApp(root)
    if hasattr(app, "db_path"):
        app.db_path = test_db

    try:
        yield app
    finally:
        # Cancel any scheduled .after() tasks
        try:
            for after_id in root.tk.eval("after info").split():
                root.after_cancel(after_id)
        except Exception:
            pass

        # Close database connection
        if hasattr(app, "conn") and app.conn:
            try:
                app.conn.close()
            except Exception:
                pass

        # Destroy root window
        try:
            root.update_idletasks()
            root.destroy()
        except Exception:
            pass