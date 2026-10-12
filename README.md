# Gym App

Gym Fitness & Performance is a desktop application built with Python, Tkinter, and SQLite for fitness trainers and administrators to manage client profiles, track weekly progress, log workouts and exercises, generate AI-style training plans, and export professional PDF client reports.

## Features

- Client profile management
- Weekly adherence tracking
- Workout and exercise logging
- AI-style training program generation
- PDF report export
- Membership status tracking
- SQLite database storage

## Requirements

- Python 3.8+
- Tkinter (included with most Python installations)
- SQLite3 (included with Python)
- pip for installing Python packages

## Installation

1. Clone the repository:

   bash
   git clone https://github.com/keerthivasanbits/Gymapp.git

   cd Gymapp
   

3. Create and activate a virtual environment (optional but recommended):

   bash
   python3 -m venv .venv
   source .venv/bin/activate
   

4. Install the required dependencies:

   bash
   pip install -r requirements.txt
   

   If you are installing manually instead of using the requirements file:

   bash
   pip install matplotlib fpdf
   

   On Linux, you may also need the Tkinter system package:

   bash
   sudo apt-get install python3-tk
   

## Run the Application

bash
python3 aceest_app.py


If you are on Windows, you can also run:

bash
python aceest_app.py


## Default Login

- Username: admin
- Password: admin

## Notes

- The app automatically creates the SQLite database file (aceest_fitness.db) when it starts for the first time.
- The application is designed for local desktop use and is not a web app.
