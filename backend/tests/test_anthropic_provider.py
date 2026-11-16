"""Tests the tool-use loop with a fake client, so no API key or network is needed."""

from types import SimpleNamespace as NS

from app.data import DEMO_STUDENT_ID
from app.llm import AnthropicProvider


def text(t):
    return NS(type="text", text=t)


def tool_use(id_, name, input_):
    return NS(type="tool_use", id=id_, name=name, input=input_)


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs["messages"][:])
        return self._responses.pop(0)


def test_tool_loop_runs_tool_and_returns_final_text():
    client = FakeClient([
        NS(stop_reason="tool_use", content=[text("Checking."), tool_use("t1", "get_social_service_status", {})]),
        NS(stop_reason="end_turn", content=[text("You have 240 hours left.")]),
    ])
    result = AnthropicProvider(client=client, model="test").respond(
        [{"role": "user", "content": "How many hours of social service do I have left?"}], DEMO_STUDENT_ID
    )
    assert result.reply == "You have 240 hours left."
    assert result.tools_used == ["get_social_service_status"]
    # The second call must carry the tool_result back to the model.
    tool_result = client.calls[1][-1]["content"][0]
    assert tool_result["type"] == "tool_result" and tool_result["tool_use_id"] == "t1"
    assert '"hours_remaining": 240' in tool_result["content"]


def test_tool_errors_are_flagged_to_the_model():
    client = FakeClient([
        NS(stop_reason="tool_use", content=[tool_use("t1", "get_grade_history", {"semester": 99})]),
        NS(stop_reason="end_turn", content=[text("No grades for that semester.")]),
    ])
    AnthropicProvider(client=client, model="test").respond([{"role": "user", "content": "x"}], DEMO_STUDENT_ID)
    assert client.calls[1][-1]["content"][0]["is_error"] is True


def test_loop_gives_up_after_max_rounds():
    looping = NS(stop_reason="tool_use", content=[tool_use("t", "get_schedule", {})])
    client = FakeClient([looping] * AnthropicProvider.MAX_TOOL_ROUNDS)
    result = AnthropicProvider(client=client, model="test").respond([{"role": "user", "content": "x"}], DEMO_STUDENT_ID)
    assert "couldn't finish" in result.reply
