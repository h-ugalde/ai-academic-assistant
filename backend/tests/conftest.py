import pytest
from fastapi.testclient import TestClient

from app import main, tools
from app.llm import OfflineProvider


@pytest.fixture
def client():
    main._sessions.clear()
    tools.SUBMITTED_REQUESTS.clear()
    main.app.dependency_overrides[main.get_provider] = lambda: OfflineProvider()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()
