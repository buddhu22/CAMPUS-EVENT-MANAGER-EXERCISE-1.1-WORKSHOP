import csv
import json
import logging
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR  = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "registrations.json"
CSV_FILE  = DATA_DIR / "attendance.csv"
LOG_FILE  = LOG_DIR  / "app.log"

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ─── Global in-memory storage ─────────────────────────────────────────────────
events        = {}   # {"E101": {"name": "Tech Workshop", "capacity": 50}}
registrations = []   # [{"event_id": "E101", "participant_id": "P001", "name": "Alice", "email": "..."}]


def save_data():
    """Persist events and registrations to JSON."""
    data = {"events": events, "registrations": registrations}
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error("Failed to save data: %s", e)


def load_data():
    """Load from JSON safely — handles missing/corrupted file."""
    global events, registrations

    if not DATA_FILE.exists():
        logging.warning("registrations.json not found. Initializing with empty data.")
        events, registrations = {}, []
        return

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Root JSON structure must be an object.")

        events        = data.get("events", {})
        registrations = data.get("registrations", [])

        if not isinstance(events, dict) or not isinstance(registrations, list):
            raise ValueError("Invalid internal data structure in JSON.")

        logging.info("Data loaded successfully.")

    except (json.JSONDecodeError, ValueError) as e:
        print("Warning: registrations.json is corrupted or malformed. Starting with empty data.")
        logging.error("Corrupted or malformed registrations.json: %s", e)
        events, registrations = {}, []
    except Exception as e:
        print("Error reading registrations.json: %s. Starting with empty data." % e)
        logging.error("Error loading registrations.json: %s", e)
        events, registrations = {}, []



def add_event_api(event_id, event_name, capacity_str):
    """Validate and add a new event."""
    event_id     = (event_id     or "").strip()
    event_name   = (event_name   or "").strip()
    capacity_str = (capacity_str or "").strip()

    if not event_id:
        logging.warning("Event creation failed: Empty Event ID.")
        return {"ok": False, "message": "Event ID cannot be empty."}

    if event_id in events:
        logging.warning("Event creation failed: Duplicate Event ID '%s'.", event_id)
        return {"ok": False, "message": "Event ID '%s' already exists." % event_id}

    if not event_name:
        logging.warning("Event creation failed: Empty Event Name.")
        return {"ok": False, "message": "Event name cannot be empty."}

    if not capacity_str:
        logging.warning("Event creation failed: Empty capacity.")
        return {"ok": False, "message": "Capacity cannot be empty."}

    try:
        capacity = int(capacity_str)
        if capacity <= 0:
            raise ValueError("non-positive")
    except ValueError:
        logging.warning("Event creation failed: Invalid capacity '%s'.", capacity_str)
        return {"ok": False, "message": "Capacity must be a positive integer."}

    events[event_id] = {"name": event_name, "capacity": capacity}
    save_data()
    logging.info("Event created: ID='%s', Name='%s', Capacity=%d.", event_id, event_name, capacity)
    return {"ok": True, "message": "Event '%s' (ID: %s) added successfully!" % (event_name, event_id)}


def register_participant_api(event_id, participant_id, name, email):
    """Validate and register a participant."""
    event_id       = (event_id       or "").strip()
    participant_id = (participant_id or "").strip()
    name           = (name           or "").strip()
    email          = (email          or "").strip()

    if not event_id or not participant_id or not name or not email:
        logging.warning("Registration failed: Empty input field(s).")
        return {"ok": False, "message": "All fields are required."}

    if event_id not in events:
        logging.warning("Registration failed: Non-existent Event ID '%s'.", event_id)
        return {"ok": False, "message": "Event does not exist."}

    if not (participant_id.startswith("P") and len(participant_id) == 4
            and participant_id[1:].isdigit()):
        logging.warning("Registration failed: Invalid participant ID '%s'.", participant_id)
        return {"ok": False, "message": "Invalid participant ID. Use format P001."}

    if "@" not in email or "." not in email.split("@")[-1]:
        logging.warning("Registration failed: Invalid email '%s'.", email)
        return {"ok": False, "message": "Invalid email address."}

    for reg in registrations:
        if reg["event_id"] == event_id and reg["participant_id"] == participant_id:
            logging.warning("Duplicate registration: '%s' for Event '%s'.", participant_id, event_id)
            return {"ok": False, "message": "Participant already registered for this event."}

    event   = events[event_id]
    current = sum(1 for r in registrations if r["event_id"] == event_id)
    if current >= event["capacity"]:
        logging.warning("Registration failed: Event '%s' is full.", event_id)
        return {"ok": False, "message": "Event is full."}

    registrations.append({
        "event_id":       event_id,
        "participant_id": participant_id,
        "name":           name,
        "email":          email
    })
    save_data()
    logging.info("Registered: '%s' (%s) to Event '%s'.", participant_id, name, event_id)
    return {"ok": True, "message": "Participant registered successfully!"}


def cancel_registration_api(event_id, participant_id):
    """Cancel a registration."""
    event_id       = (event_id       or "").strip()
    participant_id = (participant_id or "").strip()

    if not event_id or not participant_id:
        logging.warning("Cancellation failed: Empty Event ID or Participant ID.")
        return {"ok": False, "message": "Event ID and Participant ID cannot be empty."}

    for index, reg in enumerate(registrations):
        if reg["event_id"] == event_id and reg["participant_id"] == participant_id:
            registrations.pop(index)
            save_data()
            logging.info("Cancelled: '%s' from Event '%s'.", participant_id, event_id)
            return {"ok": True, "message": "Registration cancelled successfully."}

    logging.warning("Cancellation failed: Not found — '%s' in Event '%s'.", participant_id, event_id)
    return {"ok": False, "message": "Registration not found."}


def get_event_summary():
    """Return list of dicts with per-event registration counts."""
    summary = []
    for event_id, event in events.items():
        registered = sum(1 for r in registrations if r["event_id"] == event_id)
        summary.append({
            "event_id":        event_id,
            "name":            event["name"],
            "capacity":        event["capacity"],
            "registered":      registered,
            "available_seats": event["capacity"] - registered
        })
    return summary


def export_csv_data():
    """Write attendance CSV and return result dict."""
    if not registrations:
        return {"ok": False, "message": "No registrations to export."}

    try:
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Event ID", "Event Name",
                             "Participant ID", "Participant Name", "Email"])
            for reg in registrations:
                event_name = events.get(reg["event_id"], {}).get("name", "Unknown")
                writer.writerow([reg["event_id"], event_name,
                                 reg["participant_id"], reg["name"], reg["email"]])
        logging.info("Attendance CSV exported: %s", CSV_FILE)
        return {"ok": True, "message": "Attendance exported successfully."}
    except Exception as e:
        logging.error("CSV export failed: %s", e)
        return {"ok": False, "message": "Export failed: %s" % e}


def get_recent_logs(n=50):
    """Return the last n log lines, newest first."""
    if not LOG_FILE.exists():
        return []
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        return [line.rstrip() for line in lines[-n:]][::-1]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  CLI — thin wrappers around the API functions
# ══════════════════════════════════════════════════════════════════════════════

def _cli_add_event():
    print("\n--- Add Event ---")
    result = add_event_api(
        input("Enter event ID: "),
        input("Enter event name: "),
        input("Enter event capacity: ")
    )
    print(("" if result["ok"] else "Error: ") + result["message"])


def _cli_register_participant():
    print("\n--- Register Participant ---")
    result = register_participant_api(
        input("Enter event ID: "),
        input("Enter participant ID: "),
        input("Enter participant name: "),
        input("Enter email: ")
    )
    print(("" if result["ok"] else "Error: ") + result["message"])


def _cli_cancel_registration():
    print("\n--- Cancel Registration ---")
    result = cancel_registration_api(
        input("Enter event ID: "),
        input("Enter participant ID: ")
    )
    print(("" if result["ok"] else "Error: ") + result["message"])


def _cli_list_registrations():
    print("\n--- Registrations ---")
    if not registrations:
        print("No registrations found.")
        return
    for idx, reg in enumerate(registrations, 1):
        event_name = events.get(reg["event_id"], {}).get("name", "Unknown Event")
        print("%d. Event: %s (%s) | Participant ID: %s | Name: %s | Email: %s"
              % (idx, reg["event_id"], event_name,
                 reg["participant_id"], reg["name"], reg["email"]))


def _cli_show_event_summary():
    print("\n--- Event Summary ---")
    for item in get_event_summary():
        print("\nEvent ID: %s\nEvent Name: %s\nCapacity: %d\nRegistrations: %d\nAvailable Seats: %d"
              % (item["event_id"], item["name"], item["capacity"],
                 item["registered"], item["available_seats"]))


def main():
    """CLI entry point."""
    load_data()

    while True:
        print("\n===== Campus Event Registration =====")
        print("1. Add Event")
        print("2. Register Participant")
        print("3. Cancel Registration")
        print("4. List Registrations")
        print("5. Export Attendance to CSV")
        print("6. Event Summary")
        print("7. Exit")

        choice = input("Enter your choice: ").strip()

        if   choice == "1": _cli_add_event()
        elif choice == "2": _cli_register_participant()
        elif choice == "3": _cli_cancel_registration()
        elif choice == "4": _cli_list_registrations()
        elif choice == "5":
            result = export_csv_data()
            print(("" if result["ok"] else "Error: ") + result["message"])
        elif choice == "6": _cli_show_event_summary()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Error: Invalid choice!")
            logging.warning("Invalid menu choice entered: '%s'.", choice)


if __name__ == "__main__":
    main()