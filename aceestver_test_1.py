import importlib.util
from pathlib import Path
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
    """Fixture that initializes Tk root and the ACEestApp, then tears it down."""
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tkinter display not available (headless environment)")

    # Withdraw window to prevent UI popup during tests
    root.withdraw()

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
    # Generate Tk event
    app.prog_menu.event_generate("<<ComboboxSelected>>")
    app.root.update_idletasks()

    assert app.work_label.cget("text") == app.programs[target_program]["workout"]
    assert app.diet_label.cget("text") == app.programs[target_program]["diet"]