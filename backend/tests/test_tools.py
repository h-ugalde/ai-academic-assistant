from app import tools
from app.data import DEMO_STUDENT_ID


def test_schedule_lists_classrooms():
    data = tools.dispatch("get_schedule", {}, DEMO_STUDENT_ID)
    assert any(c["classroom"] == "B-204" for c in data["classes"])


def test_current_grades_average():
    data = tools.dispatch("get_current_grades", {}, DEMO_STUDENT_ID)
    mobile = next(c for c in data["courses"] if c["course"] == "Mobile Application Development")
    assert mobile["average_so_far"] == 9.25


def test_grade_history_sorted_and_filtered():
    all_sems = tools.dispatch("get_grade_history", {}, DEMO_STUDENT_ID)["semesters"]
    assert [s["semester"] for s in all_sems] == [3, 4, 5]
    one = tools.dispatch("get_grade_history", {"semester": 4}, DEMO_STUDENT_ID)["semesters"]
    assert len(one) == 1 and one[0]["average"] == 8.25


def test_grade_history_unknown_semester():
    assert "error" in tools.dispatch("get_grade_history", {"semester": 99}, DEMO_STUDENT_ID)


def test_social_service_remaining_hours():
    assert tools.dispatch("get_social_service_status", {}, DEMO_STUDENT_ID)["hours_remaining"] == 240


def test_billing_total_pending():
    assert tools.dispatch("get_tuition_billing", {}, DEMO_STUDENT_ID)["total_pending_mxn"] == 60.0


def test_submit_request_creates_ticket():
    tools.SUBMITTED_REQUESTS.clear()
    ticket = tools.dispatch("submit_service_request", {"request_type": "grade_report"}, DEMO_STUDENT_ID)
    assert ticket["ticket_id"].startswith("REQ-") and ticket["status"] == "received"


def test_submit_request_rejects_unknown_type():
    assert "error" in tools.dispatch("submit_service_request", {"request_type": "pizza"}, DEMO_STUDENT_ID)


def test_unknown_tool_and_student_are_errors_not_exceptions():
    assert "error" in tools.dispatch("drop_database", {}, DEMO_STUDENT_ID)
    assert "error" in tools.dispatch("get_schedule", {}, "nobody")


def test_model_cannot_override_student():
    # A model that tries to smuggle in another student gets an error, not data.
    result = tools.dispatch("get_schedule", {"student": {"name": "Eve"}}, DEMO_STUDENT_ID)
    assert "error" in result
