"""
web_app.py — Flask web interface for Campus Event Registration.

Imports application logic from app.py (no business logic here).
Run with:  python web_app.py
"""

from flask import (Flask, render_template, request,
                   redirect, url_for, flash, send_file)
import app as core          # reuse existing application logic

# Initialise Flask
web = Flask(__name__)
web.secret_key = "campus-event-reg-2025-secret"   # required for flash messages

# Load data once at startup
core.load_data()


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@web.route("/")
def dashboard():
    summary = core.get_event_summary()
    total_events        = len(core.events)
    total_registrations = len(core.registrations)
    total_available     = sum(item["available_seats"] for item in summary)
    return render_template(
        "dashboard.html",
        summary=summary,
        total_events=total_events,
        total_registrations=total_registrations,
        total_available=total_available
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ADD EVENT
# ─────────────────────────────────────────────────────────────────────────────

@web.route("/add-event", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":
        result = core.add_event_api(
            request.form.get("event_id", ""),
            request.form.get("event_name", ""),
            request.form.get("capacity", "")
        )
        if result["ok"]:
            flash(result["message"], "success")
            return redirect(url_for("dashboard"))
        else:
            flash(result["message"], "error")

    return render_template("add_event.html")


# ─────────────────────────────────────────────────────────────────────────────
#  REGISTER PARTICIPANT
# ─────────────────────────────────────────────────────────────────────────────

@web.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        result = core.register_participant_api(
            request.form.get("event_id", ""),
            request.form.get("participant_id", ""),
            request.form.get("name", ""),
            request.form.get("email", "")
        )
        if result["ok"]:
            flash(result["message"], "success")
            return redirect(url_for("registrations"))
        else:
            flash(result["message"], "error")

    return render_template("register.html", events=core.events)


# ─────────────────────────────────────────────────────────────────────────────
#  REGISTRATIONS LIST + CANCEL
# ─────────────────────────────────────────────────────────────────────────────

@web.route("/registrations")
def registrations():
    reg_list = []
    for reg in core.registrations:
        event_name = core.events.get(reg["event_id"], {}).get("name", "Unknown Event")
        reg_list.append({**reg, "event_name": event_name})
    return render_template("registrations.html", registrations=reg_list)


@web.route("/cancel", methods=["POST"])
def cancel():
    result = core.cancel_registration_api(
        request.form.get("event_id", ""),
        request.form.get("participant_id", "")
    )
    if result["ok"]:
        flash(result["message"], "success")
    else:
        flash(result["message"], "error")
    return redirect(url_for("registrations"))


# ─────────────────────────────────────────────────────────────────────────────
#  ATTENDANCE
# ─────────────────────────────────────────────────────────────────────────────

@web.route("/attendance")
def attendance():
    att_list = []
    for reg in core.registrations:
        event_name = core.events.get(reg["event_id"], {}).get("name", "Unknown Event")
        att_list.append({**reg, "event_name": event_name})
    return render_template("attendance.html", records=att_list)


@web.route("/export-csv", methods=["POST"])
def export_csv():
    result = core.export_csv_data()
    if result["ok"]:
        # Send file to browser as a download
        return send_file(
            core.CSV_FILE,
            as_attachment=True,
            download_name="attendance.csv",
            mimetype="text/csv"
        )
    else:
        flash(result["message"], "error")
        return redirect(url_for("attendance"))


# ─────────────────────────────────────────────────────────────────────────────
#  EVENT SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

@web.route("/summary")
def summary():
    data = core.get_event_summary()
    return render_template("summary.html", summary=data)


# ─────────────────────────────────────────────────────────────────────────────
#  LOGS (recent entries only — no sensitive data)
# ─────────────────────────────────────────────────────────────────────────────

@web.route("/logs")
def logs():
    entries = core.get_recent_logs(n=50)
    return render_template("logs.html", entries=entries)


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    web.run(debug=False, port=5000)
