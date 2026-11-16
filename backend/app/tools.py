"""Tools the assistant can call.

Design rule: the student id is never a tool argument. It comes from the
authenticated request and is injected by `dispatch`, so the language model can
only ever read the records of the student who is logged in.
"""

from __future__ import annotations

from itertools import count
from statistics import mean
from typing import Any, Callable

from .data import STUDENTS

REQUEST_TYPES = ("enrollment_certificate", "grade_report", "social_service_letter", "tuition_receipt")

# In-memory ticket store. A real deployment would write to the university's
# request system or a database.
_ticket_numbers = count(1)
SUBMITTED_REQUESTS: list[dict] = []


def get_schedule(student: dict, **_: Any) -> dict:
    return {"semester": student["semester"], "classes": student["schedule"]}


def get_current_grades(student: dict, **_: Any) -> dict:
    courses = []
    for item in student["current_grades"]:
        courses.append(
            {
                "course": item["course"],
                "partials": item["partials"],
                "average_so_far": round(mean(item["partials"]), 2),
            }
        )
    return {"semester": student["semester"], "courses": courses}


def get_grade_history(student: dict, semester: int | None = None, **_: Any) -> dict:
    history = sorted(student["grade_history"], key=lambda s: s["semester"])
    if semester is not None:
        history = [s for s in history if s["semester"] == semester]
        if not history:
            return {"error": f"No grades found for semester {semester}."}
    semesters = []
    for entry in history:
        grades = [c["grade"] for c in entry["courses"]]
        semesters.append({**entry, "average": round(mean(grades), 2)})
    return {"semesters": semesters}


def get_social_service_status(student: dict, **_: Any) -> dict:
    info = dict(student["social_service"])
    info["hours_remaining"] = info["hours_required"] - info["hours_completed"]
    return info


def get_optative_curriculum(student: dict, **_: Any) -> dict:
    info = dict(student["optative_curriculum"])
    info["credits_remaining"] = info["credits_required"] - info["credits_completed"]
    return info


def get_tuition_billing(student: dict, **_: Any) -> dict:
    pending = [b for b in student["billing"] if b["status"] == "pending"]
    return {
        "charges": student["billing"],
        "total_pending_mxn": round(sum(b["amount_mxn"] for b in pending), 2),
    }


def submit_service_request(student: dict, request_type: str = "", notes: str = "", **_: Any) -> dict:
    if request_type not in REQUEST_TYPES:
        return {"error": f"Unknown request type. Valid types: {', '.join(REQUEST_TYPES)}."}
    ticket = {
        "ticket_id": f"REQ-{next(_ticket_numbers):04d}",
        "student": student["name"],
        "request_type": request_type,
        "notes": notes[:500],
        "status": "received",
    }
    SUBMITTED_REQUESTS.append(ticket)
    return ticket


_NO_ARGS = {"type": "object", "properties": {}, "required": []}

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_schedule",
        "description": "Get the student's current class schedule: courses, days, times, buildings and classrooms.",
        "input_schema": _NO_ARGS,
    },
    {
        "name": "get_current_grades",
        "description": "Get the partial grades and running average for each course in the semester in progress.",
        "input_schema": _NO_ARGS,
    },
    {
        "name": "get_grade_history",
        "description": "Get final grades from previous semesters. Pass `semester` to get just one; omit it for all of them.",
        "input_schema": {
            "type": "object",
            "properties": {"semester": {"type": "integer", "description": "Semester number, e.g. 4."}},
            "required": [],
        },
    },
    {
        "name": "get_social_service_status",
        "description": "Get the student's social service status: hours completed, hours remaining and organization.",
        "input_schema": _NO_ARGS,
    },
    {
        "name": "get_optative_curriculum",
        "description": "Get optative (elective) course progress: credits completed, enrolled courses and available options.",
        "input_schema": _NO_ARGS,
    },
    {
        "name": "get_tuition_billing",
        "description": "Get fees and charges with their payment status, plus the total still pending.",
        "input_schema": _NO_ARGS,
    },
    {
        "name": "submit_service_request",
        "description": "Submit a request to the school administration on the student's behalf. Only call this when the student clearly asks to submit a request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_type": {"type": "string", "enum": list(REQUEST_TYPES)},
                "notes": {"type": "string", "description": "Optional extra details from the student."},
            },
            "required": ["request_type"],
        },
    },
]

_TOOLS: dict[str, Callable[..., dict]] = {
    "get_schedule": get_schedule,
    "get_current_grades": get_current_grades,
    "get_grade_history": get_grade_history,
    "get_social_service_status": get_social_service_status,
    "get_optative_curriculum": get_optative_curriculum,
    "get_tuition_billing": get_tuition_billing,
    "submit_service_request": submit_service_request,
}


def dispatch(name: str, arguments: dict | None, student_id: str) -> dict:
    """Run a tool for the authenticated student. Never raises; errors come back as data."""
    tool = _TOOLS.get(name)
    if tool is None:
        return {"error": f"Unknown tool: {name}"}
    student = STUDENTS.get(student_id)
    if student is None:
        return {"error": "Unknown student."}
    try:
        return tool(student, **(arguments or {}))
    except TypeError as exc:  # wrong argument names or types from the model
        return {"error": f"Invalid arguments for {name}: {exc}"}
