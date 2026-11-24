# ACEest Fitness & Performance

ACEest Fitness & Performance is a desktop fitness management application built with Python, Tkinter, and SQLite. It is designed for trainers and administrators to manage client records, monitor adherence, log workouts, generate training plans, and export client reports.

## Features

- Role-based login system
- Client profile creation and selection
- Weekly adherence tracking
- Workout and exercise logging
- Progress charting with matplotlib
- AI-style program generation for clients
- PDF report export for each client
- Membership status and end-date tracking
- Local SQLite database storage
- Desktop dashboard interface

## Project Files

- `aceestver_gymapp.py` – main application
- `aceestver_test_1.py` – additional test or prototype script
- `aceest_fitness.db` – SQLite database created automatically on first run
- `requirements.txt` – Python dependencies
- `Dockerfile` – container setup for running the app in Docker
- `Jenkinsfile` – CI pipeline configuration

## Requirements

- Python 3.8+
- Tkinter (included with most Python installations)
- SQLite3 (included with Python)
- pip

Optional dependencies are included in `requirements.txt`.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/keerthivasanbits/Gymapp.git
   cd Gymapp
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. If you are on Linux and Tkinter is missing, install the system package:

   ```bash
   sudo apt-get install python3-tk
   ```

## Run the Application

From the project root:

```bash
python3 aceestver_gymapp.py
```

On Windows:

```bash
python aceestver_gymapp.py
```

## Login

The application creates a default admin user automatically on first run.

- Username: `admin`
- Password: `admin`

## Database

On first launch, the app creates the SQLite database file:

```bash
aceest_fitness.db
```

This file stores:

- users
- clients
- progress
- workouts
- exercises
- metrics

## Application Workflow

Once logged in, the dashboard allows you to:

- select a client
- add or update client records
- generate an AI-style training program
- view weekly adherence charts
- add workouts and exercise details
- export a client PDF report
- check membership status and renewal date

## Docker

A Dockerfile is included for containerized use.

Build the image:

```bash
docker build -t aceest-gymapp .
```

Run the app:

```bash
docker run --rm -it aceest-gymapp
```

Note: because this is a desktop Tkinter app, GUI display support may require a local X11 display or a headless setup configured for your environment.

## Notes

- This application is designed for local desktop use, not a web app.
- The project is built around a Tkinter dashboard and local SQLite storage.
- The app is intended for fitness trainers and administrators managing client progress and schedules.
