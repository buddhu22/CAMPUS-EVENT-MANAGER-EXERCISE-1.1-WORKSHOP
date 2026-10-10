# Campus Event Registration

A simple Flask-based event registration system for managing campus events, participant registrations, attendance exports, and event summaries.

## Features

- Add new campus events with a unique event ID and capacity
- Register participants with validation for event ID, participant ID, and email
- Prevent duplicate registrations and full-event registration
- Cancel registrations
- View summary statistics for all events
- Export attendance records to CSV
- Review application logs
- Persist data in JSON files for local storage

## Tech Stack

- Python 3
- Flask
- HTML/CSS templates

## Project Structure

- `app.py` — core application logic and data persistence
- `web_app.py` — Flask routes and UI entry point
- `templates/` — HTML pages for the web interface
- `static/style.css` — styling for the app
- `data/` — JSON and CSV data files
- `logs/` — application logs

## Requirements

Install Flask if it is not already available:

```bash
pip install flask
```

## Run the Application

From the project folder:

```bash
python web_app.py
```

```

## Web Pages

- Dashboard
- Add Event
- Register Participant
- Registrations
- Attendance
- Event Summary
- Logs

## Data Storage

The application stores event and registration data in:

- `data/registrations.json`
- `data/attendance.csv`

## Notes

This project was created as part of a campus event management workshop exercise and is designed for local use and learning purposes.
