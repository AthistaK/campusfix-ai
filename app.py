from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)
DB = "campusfix.db"

CATEGORIES = {
    "Network": ["wifi", "wi-fi", "internet", "network", "router", "connection"],
    "Water": ["water", "tap", "leak", "leaking", "supply"],
    "Electricity": ["electric", "electricity", "power", "light", "switch", "socket"],
    "Cleanliness": ["dirty", "garbage", "trash", "clean", "hygiene", "washroom"],
    "Security": ["security", "unsafe", "threat", "fight", "harassment", "gate"],
    "Food / Cafeteria": ["food", "cafeteria", "canteen", "meal", "hygiene"],
    "Classroom Equipment": ["projector", "ac", "air conditioning", "fan", "equipment", "computer"],
    "Transport": ["bus", "transport", "parking", "shuttle"],
    "Infrastructure": ["road", "building", "classroom", "infrastructure", "bench"],
    "Other": []
}
CATEGORY_DEPARTMENTS = {
    "Network": {
        "department": "IT Services",
        "person": "Campus IT Helpdesk",
        "email": "it@campus.edu",
        "phone": "9000000001"
    },

    "Water": {
        "department": "Maintenance",
        "person": "Campus Maintenance Desk",
        "email": "maintenance@campus.edu",
        "phone": "9000000002"
    },

    "Electricity": {
        "department": "Maintenance",
        "person": "Campus Maintenance Desk",
        "email": "maintenance@campus.edu",
        "phone": "9000000002"
    },

    "Classroom Equipment": {
        "department": "Maintenance",
        "person": "Campus Maintenance Desk",
        "email": "maintenance@campus.edu",
        "phone": "9000000002"
    },

    "Cleanliness": {
        "department": "Maintenance",
        "person": "Campus Maintenance Desk",
        "email": "maintenance@campus.edu",
        "phone": "9000000002"
    },

    "Security": {
        "department": "Security",
        "person": "Campus Security Desk",
        "email": "security@campus.edu",
        "phone": "9000000003"
    },

    "Transport": {
        "department": "Transport Office",
        "person": "Campus Transport Desk",
        "email": "transport@campus.edu",
        "phone": "9000000004"
    },

    "Food / Cafeteria": {
        "department": "Cafeteria Management",
        "person": "Cafeteria Management Desk",
        "email": "cafeteria@campus.edu",
        "phone": "9000000005"
    },

    "Infrastructure": {
        "department": "Infrastructure & Maintenance",
        "person": "Campus Maintenance Desk",
        "email": "maintenance@campus.edu",
        "phone": "9000000002"
    },

    "Other": {
        "department": "Student Support",
        "person": "Student Support Desk",
        "email": "support@campus.edu",
        "phone": "9000000006"
    }
}
def get_department_assignment(category):
    return CATEGORY_DEPARTMENTS.get(
        category,
        CATEGORY_DEPARTMENTS["Other"]
    )
LOCATION_WEIGHTS = {
    "CSE Block": 20,
    "Library": 18,
    "Hostel A": 18,
    "Hostel B": 18,
    "Main Gate": 15,
    "Cafeteria": 12,
    "Sports Complex": 10,
    "Other": 8,
}

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        severity TEXT NOT NULL,
        priority INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Reported',
        report_count INTEGER NOT NULL DEFAULT 1,
        assigned_department TEXT DEFAULT 'Unassigned',
        assigned_person TEXT DEFAULT '',
        assigned_email TEXT DEFAULT '',
        assigned_phone TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        severity TEXT NOT NULL,
        similarity REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES incidents(id)
    );

    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        course TEXT DEFAULT 'CSE',
        year TEXT DEFAULT '1st Year',
        email TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS incident_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES incidents(id)
    );
    """)
    # Add assignment fields to older databases safely
    existing_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(incidents)"
        ).fetchall()
    }

    assignment_columns = {
    "assigned_department": "TEXT DEFAULT 'Unassigned'",
    "assigned_person": "TEXT DEFAULT ''",
    "assigned_email": "TEXT DEFAULT ''",
    "assigned_phone": "TEXT DEFAULT ''"
}

    for column, definition in assignment_columns.items():
         if column not in existing_columns:
            conn.execute(
            f"ALTER TABLE incidents ADD COLUMN {column} {definition}"
        )

    # Safe migration for databases created by the old version
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(incidents)").fetchall()
    }

    new_columns = {
        "assigned_department": "TEXT DEFAULT 'Unassigned'",
        "assigned_person": "TEXT DEFAULT ''",
        "assigned_email": "TEXT DEFAULT ''",
        "assigned_phone": "TEXT DEFAULT ''",
    }

    for column, definition in new_columns.items():
        if column not in columns:
            conn.execute(
                f"ALTER TABLE incidents ADD COLUMN {column} {definition}"
            )

    # Demo departments / contacts
    departments = [
        (
            "IT Services",
            "Campus IT Helpdesk",
            "it@campus.edu",
            "9000000001",
        ),
        (
            "Academic Office",
            "Academic Support Desk",
            "academic@campus.edu",
            "9000000002",
        ),
        (
            "Hostel Administration",
            "Hostel Support Desk",
            "hostel@campus.edu",
            "9000000003",
        ),
        (
            "Maintenance",
            "Campus Maintenance Desk",
            "maintenance@campus.edu",
            "9000000004",
        ),
        (
            "Security",
            "Campus Security Desk",
            "security@campus.edu",
            "9000000005",
        ),
        (
            "Cafeteria",
            "Cafeteria Management",
            "cafeteria@campus.edu",
            "9000000006",
        ),
    ]

    for department, person, email, phone in departments:
        conn.execute("""
            UPDATE incidents
            SET
                assigned_department = ?,
                assigned_person = ?,
                assigned_email = ?,
                assigned_phone = ?
            WHERE category = ?
              AND (assigned_department IS NULL
                   OR assigned_department = ''
                   OR assigned_department = 'Unassigned')
        """, (
            department,
            person,
            email,
            phone,
            category_to_department(category=None)
            if False else ""
        ))

    count = conn.execute(
        "SELECT COUNT(*) FROM incidents"
    ).fetchone()[0]

    if count == 0:
        seed_demo_data(conn)

    conn.commit()
    conn.close()
def seed_demo_data(conn):
    demo = [
        ("CSE Block Wi-Fi Outage", "Internet is unavailable on the second floor of the CSE block.", "Network", "CSE Block", "High", 94, 17),
        ("Hostel B Water Supply", "Water supply is unavailable in Hostel B.", "Water", "Hostel B", "Critical", 91, 9),
        ("Library AC Failure", "Air conditioning is not working in the central library.", "Classroom Equipment", "Library", "Medium", 72, 4),
        ("Cafeteria Hygiene Issue", "Students reported a cleanliness issue in the cafeteria.", "Food / Cafeteria", "Cafeteria", "High", 78, 6),
        ("Parking Light Failure", "Two lights are not working near the parking area.", "Electricity", "Main Gate", "Low", 54, 2),
    ]
    for title, desc, cat, loc, sev, priority, reports in demo:
        cur = conn.execute(
            """INSERT INTO incidents
            (title, description, category, location, severity, priority, status, report_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Investigating', ?, ?, ?)""",
            (title, desc, cat, loc, sev, priority, reports, now(), now())
        )
        incident_id = cur.lastrowid
        for i in range(reports):
            conn.execute(
                """INSERT INTO reports
                (incident_id, student_name, description, category, location, severity, similarity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (incident_id, f"Student {i+1}", desc, cat, loc, sev, 0.85 if i else 1.0, now())
            )

def classify(text):
    text = text.lower()
    scores = {}
    for category, words in CATEGORIES.items():
        scores[category] = sum(1 for word in words if word in text)
    category = max(scores, key=scores.get)
    if scores[category] == 0:
        category = "Other"
    return category, round(min(0.99, 0.60 + scores[category] * 0.08), 2)

def severity(text):
    t = text.lower()
    critical = ["fire", "danger", "electrical hazard", "security threat", "injury", "emergency"]
    high = ["completely", "outage", "no water", "not working", "broken", "unsafe", "unavailable"]
    if any(x in t for x in critical):
        return "Critical"
    if any(x in t for x in high):
        return "High"
    if len(t.split()) > 12:
        return "Medium"
    return "Low"

def normalize(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def similarity(a, b):
    aa, bb = normalize(a), normalize(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)

def calculate_priority(sev, report_count, location, description):
    sev_points = {"Low": 15, "Medium": 25, "High": 35, "Critical": 45}
    report_points = min(30, 8 + report_count * 2)
    location_points = LOCATION_WEIGHTS.get(location, 8)
    safety_bonus = 10 if any(x in description.lower() for x in ["danger", "fire", "unsafe", "hazard"]) else 0
    return min(100, sev_points[sev] + report_points + location_points + safety_bonus)

def find_matching_incident(category, location, description):
    conn = get_db()
    incidents = conn.execute(
        "SELECT * FROM incidents WHERE status != 'Resolved' AND category = ?",
        (category,)
    ).fetchall()
    conn.close()

    best = None
    best_score = 0
    for incident in incidents:
        location_match = 1.0 if incident["location"] == location else 0.0
        text_score = similarity(description, incident["description"])
        score = 0.65 * text_score + 0.35 * location_match
        if score > best_score:
            best_score = score
            best = incident
    if best and best_score >= 0.42:
        return best, round(best_score * 100, 1)
    return None, round(best_score * 100, 1)

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/api/incidents")
def incidents():
    conn = get_db()
    rows = conn.execute("SELECT * FROM incidents ORDER BY priority DESC, updated_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.get("/api/incidents/<int:incident_id>")
def incident_detail(incident_id):
    conn = get_db()

    incident = conn.execute(
        "SELECT * FROM incidents WHERE id = ?",
        (incident_id,)
    ).fetchone()

    if not incident:
        conn.close()
        return jsonify({"error": "Incident not found"}), 404

    reports = conn.execute(
        "SELECT * FROM reports WHERE incident_id = ? ORDER BY created_at DESC",
        (incident_id,)
    ).fetchall()

    conn.close()

    return jsonify({
        "incident": dict(incident),
        "reports": [dict(r) for r in reports]
    })
@app.post("/api/students")
def create_student():
    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    course = (data.get("course") or "CSE").strip()
    year = (data.get("year") or "1st Year").strip()
    email = (data.get("email") or "").strip()

    if len(name) < 2:
        return jsonify({"error": "Please enter your name."}), 400

    conn = get_db()

    existing = conn.execute(
        "SELECT * FROM students WHERE name = ?", 
        (name,)
      ).fetchone()
 
    if existing:
        conn.execute(
            """
            UPDATE students
            SET course=?, year=?, email=?
            WHERE name=?
            """,
            (course, year, email, name)
        )
    else:
        conn.execute(
            """
            INSERT INTO students
            (name, course, year, email, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, course, year, email, now())
        )

    conn.commit()

    student = conn.execute(
        "SELECT * FROM students WHERE name=?",
         (name,)
    ).fetchone()

    conn.close()
 
    return jsonify({"student": dict(student)})


@app.get("/api/students/<path:name>")
def student_profile(name):
    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE name=?",
        (name,)
    ).fetchone()

    reports = conn.execute(
        """
        SELECT
            r.id,
            r.incident_id,
            r.description,
            r.category,
            r.location,
            r.created_at,
            i.title,
            i.status,
            i.priority,
            i.severity
        FROM reports r
        JOIN incidents i ON i.id = r.incident_id
        WHERE r.student_name=?
        ORDER BY r.created_at DESC
        """,
        (name,)
    ).fetchall()

    conn.close()

    if not student:
        return jsonify({
            "student": {
                "name": name,
                "course": "CSE",
                "year": "1st Year",
                "email": ""
            },
            "reports": [dict(r) for r in reports]
        })

    return jsonify({
        "student": dict(student),
        "reports": [dict(r) for r in reports]
    })
    conn = get_db()
    incident = conn.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
    reports = conn.execute(
        "SELECT * FROM reports WHERE incident_id=? ORDER BY created_at DESC",
        (incident_id,)
    ).fetchall()
    conn.close()
    if not incident:
        return jsonify({"error": "Incident not found"}), 404
    return jsonify({"incident": dict(incident), "reports": [dict(r) for r in reports]})

@app.post("/api/analyze")
def analyze():
    data = request.get_json() or {}
    description = (data.get("description") or "").strip()
    location = (data.get("location") or "Other").strip()
    student_name = (data.get("student_name") or "Anonymous Student").strip()

    if len(description) < 8:
        return jsonify({"error": "Please describe the problem in at least 8 characters."}), 400

    category, confidence = classify(description)
    sev = severity(description)
    match, match_score = find_matching_incident(category, location, description)

    if match:
        new_count = match["report_count"] + 1
        priority = calculate_priority(sev if sev != "Low" else match["severity"], new_count, location, description)
        return jsonify({
            "category": category,
            "confidence": confidence,
            "severity": sev,
            "similarity": match_score,
            "match": dict(match),
            "preview_priority": priority,
            "student_name": student_name
        })

    priority = calculate_priority(sev, 1, location, description)
    return jsonify({
        "category": category,
        "confidence": confidence,
        "severity": sev,
        "similarity": match_score,
        "match": None,
        "preview_priority": priority,
        "student_name": student_name
    })

@app.post("/api/reports")
def create_report():
    data = request.get_json() or {}
    description = (data.get("description") or "").strip()
    location = (data.get("location") or "Other").strip()
    student_name = (data.get("student_name") or "Anonymous Student").strip()

    if len(description) < 8:
        return jsonify({"error": "Description is too short."}), 400

    category, confidence = classify(description)
    assignment = get_department_assignment(category)
    sev = severity(description)
    match, match_score = find_matching_incident(category, location, description)

    conn = get_db()
    if match:
        new_count = match["report_count"] + 1
        new_priority = calculate_priority(
            sev if sev != "Low" else match["severity"],
            new_count,
            location,
            description
        )
        conn.execute(
    """UPDATE incidents
       SET
           report_count=?,
           priority=?,
           assigned_department=?,
           assigned_person=?,
           assigned_email=?,
           assigned_phone=?,
           updated_at=?
       WHERE id=?""",
    (
        new_count,
        new_priority,
        assignment["department"],
        assignment["person"],
        assignment["email"],
        assignment["phone"],
        now(),
        match["id"]
    )
)
        conn.execute(
            """INSERT INTO reports
            (incident_id, student_name, description, category, location, severity, similarity, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (match["id"], student_name, description, category, location, sev, match_score / 100, now())
        )
        conn.commit()
        conn.close()
        return jsonify({
            "message": "Report grouped with an existing incident.",
            "grouped": True,
            "incident_id": match["id"],
            "category": category,
            "severity": sev,
            "similarity": match_score,
            "priority": new_priority,
            "confidence": confidence
        })

    priority = calculate_priority(sev, 1, location, description)
    title = f"{category} issue — {location}"
    cur = conn.execute(
    """INSERT INTO incidents
    (
        title,
        description,
        category,
        location,
        severity,
        priority,
        status,
        report_count,
        assigned_department,
        assigned_person,
        assigned_email,
        assigned_phone,
        created_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, 'Reported', 1, ?, ?, ?, ?, ?, ?)""",
    (
        title,
        description,
        category,
        location,
        sev,
        priority,
        assignment["department"],
        assignment["person"],
        assignment["email"],
        assignment["phone"],
        now(),
        now()
    )
)
    incident_id = cur.lastrowid
    conn.execute(
        """INSERT INTO reports
        (incident_id, student_name, description, category, location, severity, similarity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (incident_id, student_name, description, category, location, sev, 1.0, now())
    )
    conn.commit()
    conn.close()
    return jsonify({
        "message": "New incident created.",
        "grouped": False,
        "incident_id": incident_id,
        "category": category,
        "severity": sev,
        "similarity": 0,
        "priority": priority,
        "confidence": confidence
    }), 201

@app.patch("/api/incidents/<int:incident_id>")
def update_incident(incident_id):
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ["Reported", "Investigating", "Assigned", "In Progress", "Resolved"]:
        return jsonify({"error": "Invalid status"}), 400
    conn = get_db()
    cur = conn.execute(
        "UPDATE incidents SET status=?, updated_at=? WHERE id=?",
        (status, now(), incident_id)
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Incident not found"}), 404
    return jsonify({"message": "Status updated."})

@app.get("/api/stats")
def stats():
    conn = get_db()
    active = conn.execute("SELECT COUNT(*) FROM incidents WHERE status != 'Resolved'").fetchone()[0]
    critical = conn.execute("SELECT COUNT(*) FROM incidents WHERE severity='Critical' AND status != 'Resolved'").fetchone()[0]
    reports = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='Resolved'").fetchone()[0]
    grouped = conn.execute("SELECT COALESCE(SUM(report_count),0) FROM incidents").fetchone()[0] - active
    conn.close()
    return jsonify({
        "active_incidents": active,
        "critical": critical,
        "total_reports": reports,
        "resolved": resolved,
        "unique_incidents": active + resolved
    })

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
