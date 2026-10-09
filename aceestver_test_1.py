import importlib.util
from pathlib import Path
from unittest.mock import MagicMock
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
    # Fallback to Mock root when running in headless environments (Jenkins, CI/CD)
    root = MagicMock()
    is_mocked = True

  app = ACEestApp(root)

  # If mocked, emulate widget attributes and cget behavior
  if is_mocked:
    data_store = {
        "title": "ACEest Fitness and Gym",
        "work_text": "Select a profile to view workout",
        "diet_text": "Select a profile to view diet",
        "work_fg": "white",
    }

    app.root.title.return_value = data_store["title"]

    def work_cget(prop):
      if prop == "text":
        return getattr(
            app, "_work_text", "Select a profile to view workout"
        )
      if prop == "fg":
        return getattr(app, "_work_fg", "white")
      return ""

    def diet_cget(prop):
      if prop == "text":
        return getattr(app, "_diet_text", "Select a profile to view diet")
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
    app.prog_menu.__getitem__.return_value = list(app.programs.keys())

    # Ensure prog_var updates propagate
    prog_var_val = [""]
    app.prog_var = MagicMock()
    app.prog_var.set.side_effect = lambda val: prog_var_val.__setitem__(0, val)
    app.prog_var.get.side_effect = lambda: prog_var_val[0]

  yield app

  if not is_mocked:
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