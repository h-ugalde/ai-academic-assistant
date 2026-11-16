"""Chat providers.

`AnthropicProvider` runs a tool-use loop against the Anthropic Messages API.
`OfflineProvider` is a keyword router that calls the same tools without any
network access, so the app can be demoed and tested with no API key.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from . import tools

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an academic services assistant for a university student.
Help the student check their schedule, grades, social service status, optative
(elective) courses and fees, and submit administrative requests.

Rules:
- Use the provided tools to get facts. Never invent grades, hours, amounts, rooms or dates.
- Answer in the language the student writes in (Spanish or English).
- Keep answers short and clear. Use short lists for schedules and grades.
- Only submit a request when the student clearly asks for one, and tell them the ticket id.
- If a question is outside academic services, say so politely and offer what you can help with.
- You can only see the logged-in student's records. Never discuss other students."""


@dataclass
class ChatResult:
    reply: str
    tools_used: list[str] = field(default_factory=list)


class Provider(Protocol):
    name: str

    def respond(self, history: list[dict], student_id: str) -> ChatResult:
        """`history` is a list of {"role", "content"} text turns ending with the user's message."""
        ...


class AnthropicProvider:
    name = "anthropic"
    MAX_TOOL_ROUNDS = 5

    def __init__(self, client: Any = None, model: str | None = None) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.client = client
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    def respond(self, history: list[dict], student_id: str) -> ChatResult:
        messages: list[dict] = [dict(turn) for turn in history]
        used: list[str] = []
        for _ in range(self.MAX_TOOL_ROUNDS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=tools.TOOL_SCHEMAS,
                messages=messages,
            )
            if response.stop_reason != "tool_use":
                text = "".join(block.text for block in response.content if block.type == "text")
                return ChatResult(reply=text.strip(), tools_used=used)

            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                used.append(block.name)
                output = tools.dispatch(block.name, block.input, student_id)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(output, ensure_ascii=False),
                        "is_error": "error" in output,
                    }
                )
            messages.append({"role": "user", "content": results})

        log.warning("Tool loop hit the %d-round limit", self.MAX_TOOL_ROUNDS)
        return ChatResult(reply="Sorry, I couldn't finish that request. Please try again.", tools_used=used)


# --------------------------------------------------------------------------- #
# Offline provider
# --------------------------------------------------------------------------- #

_SPANISH_HINTS = re.compile(
    r"\b(horario|calificaciones|calificación|servicio|pago|pagos|colegiatura|solicitar|solicito|constancia|"
    r"historial|optativas?|mis|cuál|cuáles|qué|cuántas|cuántos|hola|semestre|salón|adeudo)\b",
    re.IGNORECASE,
)

_LABELS = {
    "en": {
        "schedule": "Your schedule:",
        "current": "Your current grades:",
        "history": "Your grade history:",
        "avg": "average",
        "semester": "Semester",
        "ss": "Social service: {status}, {done} of {req} hours completed ({left} remaining) at {org}.",
        "opt": "Optative courses: {done} of {req} credits done ({left} to go). Enrolled: {enrolled}. Available: {avail}.",
        "bill_pending": "You have {total:.2f} MXN pending:",
        "bill_clear": "You have no pending charges.",
        "ticket": "Done. Your request ({kind}) was received with ticket {ticket}.",
        "fallback": "I can help with your schedule, grades, grade history, social service, optative courses, fees, or submitting a request. What do you need?",
        "error": "Sorry, I couldn't get that: {error}",
    },
    "es": {
        "schedule": "Tu horario:",
        "current": "Tus calificaciones actuales:",
        "history": "Tu historial de calificaciones:",
        "avg": "promedio",
        "semester": "Semestre",
        "ss": "Servicio social: {status}, {done} de {req} horas completadas (faltan {left}) en {org}.",
        "opt": "Optativas: {done} de {req} créditos completados (faltan {left}). Inscritas: {enrolled}. Disponibles: {avail}.",
        "bill_pending": "Tienes {total:.2f} MXN pendientes:",
        "bill_clear": "No tienes adeudos pendientes.",
        "ticket": "Listo. Tu solicitud ({kind}) fue recibida con el folio {ticket}.",
        "fallback": "Puedo ayudarte con tu horario, calificaciones, historial, servicio social, optativas, pagos o enviar una solicitud. ¿Qué necesitas?",
        "error": "Lo siento, no pude obtenerlo: {error}",
    },
}

_STATUS_ES = {"in_progress": "en curso", "completed": "completado", "not_started": "sin iniciar"}

_REQUEST_KEYWORDS = {
    "enrollment_certificate": ("constancia", "enrollment", "certificate"),
    "grade_report": ("kardex", "boleta", "grade report", "transcript"),
    "social_service_letter": ("carta de servicio", "social service letter"),
    "tuition_receipt": ("recibo", "receipt"),
}


class OfflineProvider:
    name = "offline"

    def respond(self, history: list[dict], student_id: str) -> ChatResult:
        text = history[-1]["content"].lower()
        lang = "es" if _SPANISH_HINTS.search(text) else "en"
        t = _LABELS[lang]

        if re.search(r"\b(solicit|request|submit|envi[ae])", text):
            kind = next(
                (k for k, words in _REQUEST_KEYWORDS.items() if any(w in text for w in words)),
                None,
            )
            if kind:
                data = tools.dispatch("submit_service_request", {"request_type": kind}, student_id)
                return self._wrap("submit_service_request", data, t, lambda d: t["ticket"].format(kind=kind, ticket=d["ticket_id"]))

        if re.search(r"historial|history|previous|anterior|kardex|semestre \d|semester \d", text):
            match = re.search(r"(?:semestre|semester)\s*(\d+)", text)
            args = {"semester": int(match.group(1))} if match else {}
            data = tools.dispatch("get_grade_history", args, student_id)
            return self._wrap("get_grade_history", data, t, lambda d: self._fmt_history(d, t))
        if re.search(r"grade|calificaci|promedio|notas", text):
            data = tools.dispatch("get_current_grades", {}, student_id)
            return self._wrap("get_current_grades", data, t, lambda d: self._fmt_current(d, t))
        if re.search(r"schedule|timetable|horario|class|clase|sal[oó]n|classroom|building|edificio", text):
            data = tools.dispatch("get_schedule", {}, student_id)
            return self._wrap("get_schedule", data, t, lambda d: self._fmt_schedule(d, t))
        if re.search(r"social service|servicio social", text):
            data = tools.dispatch("get_social_service_status", {}, student_id)
            return self._wrap(
                "get_social_service_status", data, t,
                lambda d: t["ss"].format(status=(_STATUS_ES.get(d["status"], d["status"]) if lang == "es" else d["status"].replace("_", " ")), done=d["hours_completed"], req=d["hours_required"], left=d["hours_remaining"], org=d["organization"]),
            )
        if re.search(r"optativ|elective|optative", text):
            data = tools.dispatch("get_optative_curriculum", {}, student_id)
            return self._wrap(
                "get_optative_curriculum", data, t,
                lambda d: t["opt"].format(done=d["credits_completed"], req=d["credits_required"], left=d["credits_remaining"], enrolled=", ".join(d["enrolled"]), avail=", ".join(d["available"])),
            )
        if re.search(r"\b(tuition|billing|fees?|pagos?|colegiatura|adeudo|owe)\b", text):
            data = tools.dispatch("get_tuition_billing", {}, student_id)
            return self._wrap("get_tuition_billing", data, t, lambda d: self._fmt_billing(d, t))

        return ChatResult(reply=t["fallback"])

    @staticmethod
    def _wrap(tool: str, data: dict, t: dict, fmt) -> ChatResult:
        if "error" in data:
            return ChatResult(reply=t["error"].format(error=data["error"]), tools_used=[tool])
        return ChatResult(reply=fmt(data), tools_used=[tool])

    @staticmethod
    def _fmt_schedule(d: dict, t: dict) -> str:
        lines = [t["schedule"]]
        for c in d["classes"]:
            lines.append(f"- {c['day']} {c['start']}-{c['end']}: {c['course']} ({c['building']}, {c['classroom']})")
        return "\n".join(lines)

    @staticmethod
    def _fmt_current(d: dict, t: dict) -> str:
        lines = [t["current"]]
        for c in d["courses"]:
            partials = ", ".join(str(p) for p in c["partials"])
            lines.append(f"- {c['course']}: {partials} ({t['avg']} {c['average_so_far']})")
        return "\n".join(lines)

    @staticmethod
    def _fmt_history(d: dict, t: dict) -> str:
        lines = [t["history"]]
        for s in d["semesters"]:
            lines.append(f"{t['semester']} {s['semester']} ({t['avg']} {s['average']}):")
            for c in s["courses"]:
                lines.append(f"- {c['course']}: {c['grade']}")
        return "\n".join(lines)

    @staticmethod
    def _fmt_billing(d: dict, t: dict) -> str:
        pending = [c for c in d["charges"] if c["status"] == "pending"]
        if not pending:
            return t["bill_clear"]
        lines = [t["bill_pending"].format(total=d["total_pending_mxn"])]
        for c in pending:
            lines.append(f"- {c['concept']}: {c['amount_mxn']:.2f} MXN ({c['due_date']})")
        return "\n".join(lines)


def build_provider() -> Provider:
    """Anthropic when an API key is configured, otherwise the offline demo provider."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicProvider()
    log.warning("ANTHROPIC_API_KEY not set; using the offline keyword provider.")
    return OfflineProvider()
