import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch
import tkinter as tk
from aceestver_gymapp import ACEestApp


@pytest.fixture
def app():
    """Initializes the Tk instance and ACEestApp without displaying a GUI window."""
    root = tk.Tk()
    root.withdraw()  # Prevent window rendering during test runs
    application = ACEestApp(root)
    yield application
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_initial_state(app):
    """Verifies that all input fields and display labels start with default values."""
    assert app.name_var.get() == ""
    assert app.age_var.get() == 0
    assert app.weight_var.get() == 0.0
    assert app.program_var.get() == ""
    assert app.progress_var.get() == 0
    assert app.calorie_label.cget("text") == "Estimated Calories: --"


@pytest.mark.parametrize(
    "program_name, weight, expected_factor, expected_color",
    [
        ("Fat Loss (FL)", 80.0, 22, "#e74c3c"),
        ("Muscle Gain (MG)", 70.0, 35, "#2ecc71"),
        ("Beginner (BG)", 60.0, 26, "#3498db"),
    ],
)
def test_update_program_with_weight(app, program_name, weight, expected_factor, expected_color):
    """Tests updating the workout text, diet text, and calorie calculation when weight > 0."""
    app.weight_var.set(weight)
    app.program_var.set(program_name)
    app.update_program()

    expected_calories = int(weight * expected_factor)
    assert app.calorie_label.cget("text") == f"Estimated Calories: {expected_calories} kcal"

    workout_content = app.workout_text.get("1.0", "end-1c")
    diet_content = app.diet_text.get("1.0", "end-1c")
    assert workout_content == app.programs[program_name]["workout"]
    assert diet_content == app.programs[program_name]["diet"]
    assert app.workout_text.cget("fg") == expected_color


def test_update_program_without_weight(app):
    """Calorie calculation should remain unset when weight is zero."""
    app.weight_var.set(0)
    app.program_var.set("Fat Loss (FL)")
    app.update_program()

    assert app.calorie_label.cget("text") == "Estimated Calories: --"
    assert app.workout_text.get("1.0", "end-1c") == app.programs["Fat Loss (FL)"]["workout"]


@patch("aceestver_gymapp.messagebox.showwarning")
def test_save_client_validation_missing_name(mock_warning, app):
    """Triggers warning when the client name is missing."""
    app.name_var.set("")
    app.program_var.set("Muscle Gain (MG)")
    app.save_client()

    mock_warning.assert_called_once_with("Incomplete", "Please fill client name and program.")


@patch("aceestver_gymapp.messagebox.showwarning")
def test_save_client_validation_missing_program(mock_warning, app):
    """Triggers warning when the program is missing."""
    app.name_var.set("Arun")
    app.program_var.set("")
    app.save_client()

    mock_warning.assert_called_once_with("Incomplete", "Please fill client name and program.")


@patch("aceestver_gymapp.messagebox.showinfo")
def test_save_client_success(mock_info, app):
    """Triggers success notification with formatted name and adherence percentage."""
    app.name_var.set("Kavitha")
    app.program_var.set("Beginner (BG)")
    app.progress_var.set(85)
    app.save_client()

    expected_message = "Client Kavitha saved successfully.\nAdherence: 85%"
    mock_info.assert_called_once_with("Saved", expected_message)


def test_reset_behavior(app):
    """Verifies that reset clears all variables and UI panels back to initial states."""
    app.name_var.set("Vikram")
    app.age_var.set(28)
    app.weight_var.set(75.0)
    app.program_var.set("Fat Loss (FL)")
    app.progress_var.set(90)
    app.update_program()

    app.reset()

    assert app.name_var.get() == ""
    assert app.age_var.get() == 0
    assert app.weight_var.get() == 0.0
    assert app.program_var.get() == ""
    assert app.progress_var.get() == 0
    assert app.calorie_label.cget("text") == "Estimated Calories: --"
    assert app.workout_text.get("1.0", "end-1c") == ""
    assert app.diet_text.get("1.0", "end-1c") == ""