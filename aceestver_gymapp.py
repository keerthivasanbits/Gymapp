import tkinter as tk
from tkinter import ttk, messagebox


class ACEestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ACEest Fitness and Gym")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1a1a1a")

        # Program factor and details dictionary
        self.programs = {
            "Fat Loss (FL)": {
                "workout": "Mon: 5x5 Back Squat + AMRAP\nTue: EMOM 20min Assault Bike\nWed: Bench Press + 21-15-9\nThu: 10RFT Deadlifts/Box Jumps\nFri: 30min Active Recovery",
                "diet": "B: 3 Egg Whites + Oats Idli\nL: Grilled Chicken + Brown Rice\nD: Fish Curry + Millet Roti\nTarget: 2,000 kcal",
                "color": "#e74c3c",
                "factor": 22
            },
            "Muscle Gain (MG)": {
                "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\nThu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10",
                "diet": "B: 4 Eggs + PB Oats\nL: Chicken Biryani (250g Chicken)\nD: Mutton Curry + Jeera Rice\nTarget: 3,200 kcal",
                "color": "#2ecc71",
                "factor": 35
            },
            "Beginner (BG)": {
                "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups.\nFocus: Technique Mastery & Form (90% Threshold)",
                "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\nProtein: 120g/day",
                "color": "#3498db",
                "factor": 26
            }
        }

        # Form Variables with types and initial values matching test_initial_state
        self.name_var = tk.StringVar(value="")
        self.age_var = tk.IntVar(value=0)
        self.weight_var = tk.DoubleVar(value=0.0)
        self.program_var = tk.StringVar(value="")
        self.progress_var = tk.IntVar(value=0)

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#d4af37", height=80)
        header.pack(fill="x")
        tk.Label(
            header,
            text="ACEest FUNCTIONAL FITNESS",
            font=("Helvetica", 24, "bold"),
            bg="#d4af37",
            fg="black"
        ).pack(pady=20)

        # Main Container
        main_frame = tk.Frame(self.root, bg="#1a1a1a")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Panel: Client Profile Form
        left_panel = tk.LabelFrame(
            main_frame,
            text=" Client Profile ",
            fg="#d4af37",
            bg="#1a1a1a",
            font=("Arial", 12, "bold")
        )
        left_panel.pack(side="left", fill="y", padx=10)

        tk.Label(left_panel, text="Client Name:", bg="#1a1a1a", fg="white").pack(pady=(10, 2))
        self.name_entry = tk.Entry(left_panel, textvariable=self.name_var)
        self.name_entry.pack(padx=20, pady=5, fill="x")

        tk.Label(left_panel, text="Age:", bg="#1a1a1a", fg="white").pack(pady=(10, 2))
        self.age_entry = tk.Entry(left_panel, textvariable=self.age_var)
        self.age_entry.pack(padx=20, pady=5, fill="x")

        tk.Label(left_panel, text="Weight (kg):", bg="#1a1a1a", fg="white").pack(pady=(10, 2))
        self.weight_entry = tk.Entry(left_panel, textvariable=self.weight_var)
        self.weight_entry.pack(padx=20, pady=5, fill="x")

        tk.Label(left_panel, text="Select Program:", bg="#1a1a1a", fg="white").pack(pady=(10, 2))
        self.prog_menu = ttk.Combobox(
            left_panel,
            textvariable=self.program_var,
            values=list(self.programs.keys()),
            state="readonly"
        )
        self.prog_menu.pack(padx=20, pady=5, fill="x")
        self.prog_menu.bind("<<ComboboxSelected>>", lambda e: self.update_program())

        tk.Label(left_panel, text="Adherence / Progress (%):", bg="#1a1a1a", fg="white").pack(pady=(10, 2))
        self.progress_entry = tk.Entry(left_panel, textvariable=self.progress_var)
        self.progress_entry.pack(padx=20, pady=5, fill="x")

        # Calorie Display Label
        self.calorie_label = tk.Label(
            left_panel,
            text="Estimated Calories: --",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 11, "bold")
        )
        self.calorie_label.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(left_panel, bg="#1a1a1a")
        btn_frame.pack(pady=10, fill="x", padx=20)

        self.save_btn = tk.Button(btn_frame, text="Save Client", bg="#d4af37", fg="black", command=self.save_client)
        self.save_btn.pack(fill="x", pady=4)

        self.reset_btn = tk.Button(btn_frame, text="Reset", bg="#555", fg="white", command=self.reset)
        self.reset_btn.pack(fill="x", pady=4)

        # Right Panel: Workout & Diet Displays (using tk.Text widgets)
        self.right_panel = tk.Frame(main_frame, bg="#1a1a1a")
        self.right_panel.pack(side="right", fill="both", expand=True)

        self.work_frame = tk.LabelFrame(
            self.right_panel,
            text=" Weekly Workout Chart ",
            fg="#d4af37",
            bg="#1a1a1a",
            font=("Arial", 12)
        )
        self.work_frame.pack(fill="both", expand=True, pady=5)
        self.workout_text = tk.Text(self.work_frame, bg="#1a1a1a", fg="white", font=("Arial", 11), wrap="word")
        self.workout_text.pack(fill="both", expand=True, padx=10, pady=10)

        self.diet_frame = tk.LabelFrame(
            self.right_panel,
            text=" Daily Nutrition Plan ",
            fg="#d4af37",
            bg="#1a1a1a",
            font=("Arial", 12)
        )
        self.diet_frame.pack(fill="both", expand=True, pady=5)
        self.diet_text = tk.Text(self.diet_frame, bg="#1a1a1a", fg="white", font=("Arial", 11), wrap="word")
        self.diet_text.pack(fill="both", expand=True, padx=10, pady=10)

    def update_program(self):
        selected_program = self.program_var.get()
        try:
            current_weight = float(self.weight_var.get())
        except (ValueError, tk.TclError):
            current_weight = 0.0

        if selected_program in self.programs:
            data = self.programs[selected_program]

            # Update workout Text widget and foreground color
            self.workout_text.delete("1.0", tk.END)
            self.workout_text.insert(tk.END, data["workout"])
            self.workout_text.config(fg=data["color"])

            # Update diet Text widget
            self.diet_text.delete("1.0", tk.END)
            self.diet_text.insert(tk.END, data["diet"])

            # Calorie calculation
            if current_weight > 0:
                calories = int(current_weight * data["factor"])
                self.calorie_label.config(text=f"Estimated Calories: {calories} kcal")
            else:
                self.calorie_label.config(text="Estimated Calories: --")
        else:
            self.calorie_label.config(text="Estimated Calories: --")

    def save_client(self):
        name = self.name_var.get().strip()
        program = self.program_var.get().strip()

        if not name or not program:
            messagebox.showwarning("Incomplete", "Please fill client name and program.")
            return

        adherence = self.progress_var.get()
        messagebox.showinfo("Saved", f"Client {name} saved successfully.\nAdherence: {adherence}%")

    def reset(self):
        self.name_var.set("")
        self.age_var.set(0)
        self.weight_var.set(0.0)
        self.program_var.set("")
        self.progress_var.set(0)

        self.calorie_label.config(text="Estimated Calories: --")
        self.workout_text.delete("1.0", tk.END)
        self.diet_text.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = ACEestApp(root)
    root.mainloop()