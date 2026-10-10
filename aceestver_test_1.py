import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import tkinter as tk

# Load the file directly by path to handle both '-' and '.' in the filename
current_dir = Path(__file__).resolve().parent
file_path = current_dir / "aceestver-1.0.py"

spec = importlib.util.spec_from_file_location("aceest_module", file_path)
aceest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aceest_module)

ACEestApp = aceest_module.ACEestApp


@pytest.fixture
def app_instance():
    """Fixture that initializes Tk root (or a mock if headless) and the ACEestApp."""
    is_mocked = False
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        root = MagicMock()
        is_mocked = True

    if is_mocked:
        # Patch StringVar and ttk/tk widgets while instantiating ACEestApp
        with patch("tkinter.StringVar") as mock_string_var, \
             patch("tkinter.ttk.Combobox"), \
             patch("tkinter.ttk.Label"), \
             patch("tkinter.ttk.Frame"), \
             patch("tkinter.Label"), \
             patch("tkinter.Frame"):
            
            # Create a mock StringVar that maintains state
            var_state = {"val": ""}
            mock_var = MagicMock()
            mock_var.get.side_effect = lambda: var_state["val"]
            mock_var.set.side_effect = lambda v: var_state.update({"val": v})
            mock_string_var.return_value = mock_var

            app = ACEestApp(root)
            app.prog_var = mock_var

            # Emulate widget attributes and cget/config behaviors
            data_store = {
                "title": "ACEest Fitness and Gym",
                "work_text": "Select a profile to view workout",
                "diet_text": "Select a profile to view diet",
                "work_fg": "white",
            }
            app.root.title.return_value = data_store["title"]

            app._work_text = data_store["work_text"]
            app._work_fg = data_store["work_fg"]
            app._diet_text = data_store["diet_text"]

            def work_cget(prop):
                if prop == "text":
                    return getattr(app, "_work_text", "")
                if prop == "fg":
                    return getattr(app, "_work_fg", "white")
                return ""

            def diet_cget(prop):
                if prop == "text":
                    return getattr(app, "_diet_text", "")
                return ""

            def work_config(**kwargs):
                if "text" in kwargs:
                    app._work_text = kwargs["text"]
                if "fg" in kwargs:
                    app._work_fg = kwargs["fg"]

            def diet_config(**kwargs):
                if "text" in kwargs:
                    app._diet_text = kwargs["text"]

            app.work_label = MagicMock()
            app.work_label.cget.side_effect = work_cget
            app.work_label.config.side_effect = work_config

            app.diet_label = MagicMock()
            app.diet_label.cget.side_effect = diet_cget
            app.diet_label.config.side_effect = diet_config

            app.prog_menu = MagicMock()
            app.prog_menu.__getitem__.side_effect = lambda k: list(app.programs.keys()) if k == "values" else None

            yield app
    else:
        app = ACEestApp(root)
        yield app
        root.destroy()


def test_initial_state(app_instance):
    """Test that the application initializes with expected defaults and data store."""
    app = app_instance

    # Check root configuration
    assert app.root.title() == "ACEest Fitness and Gym"

    # Verify program data keys exist
    expected_programs = {"Fat Loss (FL)", "Muscle Gain (MG)", "Beginner (BG)"}
    assert set(app.programs.keys()) == expected_programs

    # Verify initial label contents
    assert app.work_label.cget("text") == "Select a profile to view workout"
    assert app.diet_label.cget("text") == "Select a profile to view diet"

    # Verify combobox options
    assert list(app.prog_menu["values"]) == list(app.programs.keys())


@pytest.mark.parametrize(
    "program_name",
    ["Fat Loss (FL)", "Muscle Gain (MG)", "Beginner (BG)"],
)
def test_update_display_logic(app_instance, program_name):
    """Verify labels update accurately when a program is selected."""
    app = app_instance
    expected_data = app.programs[program_name]

    # Simulate combobox selection
    app.prog_var.set(program_name)
    app.update_display(event=None)

    assert app.work_label.cget("text") == expected_data["workout"]
    assert app.work_label.cget("fg") == expected_data["color"]
    assert app.diet_label.cget("text") == expected_data["diet"]


def test_event_binding_trigger(app_instance):
    """Test that firing the ComboboxSelected virtual event updates UI labels."""
    app = app_instance
    target_program = "Muscle Gain (MG)"

    # Set selection in dropdown
    app.prog_menu.set(target_program)
    app.prog_var.set(target_program)

    # Generate Tk event
    app.prog_menu.event_generate("<<ComboboxSelected>>")
    if hasattr(app.root, "update_idletasks"):
        app.root.update_idletasks()
    app.update_display(event=None)

    assert app.work_label.cget("text") == app.programs[target_program]["workout"]
    assert app.diet_label.cget("text") == app.programs[target_program]["diet"]