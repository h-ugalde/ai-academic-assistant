"""Mock academic records.

All data here is synthetic. It stands in for the university's real systems
(SAES, billing, social service office) so the project can be demoed and tested
without any personal information.
"""

from __future__ import annotations

DEMO_STUDENT_ID = "A0001"

STUDENTS: dict[str, dict] = {
    DEMO_STUDENT_ID: {
        "name": "Alex Rivera",
        "program": "Computer Systems Engineering",
        "semester": 6,
        "schedule": [
            {"course": "Mobile Application Development", "day": "Monday", "start": "08:00", "end": "10:00", "building": "Building 2", "classroom": "B-204"},
            {"course": "Mobile Application Development", "day": "Wednesday", "start": "08:00", "end": "10:00", "building": "Building 2", "classroom": "B-204"},
            {"course": "Neural Networks", "day": "Tuesday", "start": "10:00", "end": "12:00", "building": "Building 4", "classroom": "C-101"},
            {"course": "Neural Networks", "day": "Thursday", "start": "10:00", "end": "12:00", "building": "Building 4", "classroom": "C-101"},
            {"course": "Software Design", "day": "Monday", "start": "12:00", "end": "14:00", "building": "Building 1", "classroom": "A-310"},
            {"course": "Software Design", "day": "Friday", "start": "12:00", "end": "14:00", "building": "Building 1", "classroom": "A-310"},
            {"course": "Database Systems", "day": "Tuesday", "start": "08:00", "end": "10:00", "building": "Building 3", "classroom": "Lab 2"},
            {"course": "Database Systems", "day": "Thursday", "start": "08:00", "end": "10:00", "building": "Building 3", "classroom": "Lab 2"},
        ],
        # Partial grades for the semester in progress (scale 0-10).
        "current_grades": [
            {"course": "Mobile Application Development", "partials": [9.0, 9.5]},
            {"course": "Neural Networks", "partials": [8.0, 8.5]},
            {"course": "Software Design", "partials": [8.8, 9.0]},
            {"course": "Database Systems", "partials": [7.5, 8.0]},
        ],
        "grade_history": [
            {
                "semester": 4,
                "courses": [
                    {"course": "Operating Systems", "grade": 8.5},
                    {"course": "Data Structures", "grade": 9.0},
                    {"course": "Computer Networks", "grade": 8.0},
                    {"course": "Probability and Statistics", "grade": 7.5},
                ],
            },
            {
                "semester": 5,
                "courses": [
                    {"course": "Web Application Development", "grade": 9.0},
                    {"course": "Software Engineering", "grade": 8.5},
                    {"course": "Algorithms", "grade": 8.0},
                    {"course": "Artificial Intelligence", "grade": 9.5},
                ],
            },
            {
                "semester": 3,
                "courses": [
                    {"course": "Object-Oriented Programming", "grade": 9.0},
                    {"course": "Discrete Mathematics", "grade": 7.0},
                    {"course": "Computer Architecture", "grade": 8.0},
                    {"course": "Linear Algebra", "grade": 7.5},
                ],
            },
        ],
        "social_service": {
            "status": "in_progress",
            "hours_completed": 240,
            "hours_required": 480,
            "organization": "Example Consulting PyME",
            "start_date": "2026-08-03",
        },
        "optative_curriculum": {
            "credits_required": 12,
            "credits_completed": 6,
            "enrolled": ["Neural Networks"],
            "available": ["Cloud Computing", "Computer Vision", "Mobile Security", "Natural Language Processing"],
        },
        "billing": [
            {"concept": "Semester re-enrollment fee", "amount_mxn": 450.0, "due_date": "2026-08-15", "status": "paid"},
            {"concept": "Lab materials fee", "amount_mxn": 300.0, "due_date": "2026-09-30", "status": "paid"},
            {"concept": "Library fine (late return)", "amount_mxn": 60.0, "due_date": "2026-12-10", "status": "pending"},
        ],
    }
}
