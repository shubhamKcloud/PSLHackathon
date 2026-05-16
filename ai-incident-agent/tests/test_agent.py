from pathlib import Path

from ai_incident_agent.agent import AIAgent
from ai_incident_agent.analyzer import Analyzer


class MockModelClient:
    def summarize(self, prompt: str) -> str:
        return "Mocked AI analysis response"


def test_agent_runs_cycle() -> None:
    agent = AIAgent(
        log_sources=["/tmp/mock.log"],
        ticketing_config={"provider": "mock"},
        model_client=MockModelClient(),
    )

    result = agent.run_cycle()
    assert isinstance(result, dict)
    assert "incidents" in result
    assert isinstance(result["incidents"], list)


def test_knowledge_base_root_cause(tmp_path: Path) -> None:
    knowledge_base_dir = tmp_path / "knowledgeBase"
    knowledge_base_dir.mkdir()
    entry_file = knowledge_base_dir / "Authentication Failure"
    entry_file.write_text(
        "## Error Title\nAuthentication Failure\n\n"
        "## Error Description\n401 Unauthorized\n\n"
        "## Root Cause\nCredentials are expired or invalid.\n\n"
        "## Resolution\n- Refresh authentication tokens.\n- Verify usernames, passwords, and secrets.\n"
    )

    analyzer = Analyzer(MockModelClient(), knowledge_base_dir=knowledge_base_dir)
    result = analyzer.root_cause({
        "message": "401 Unauthorized access when calling the API",
        "source": "auth-service",
        "level": "error",
    })

    assert result["source"] == "knowledge_base"
    assert result["knowledge_base_entry"] == "Authentication Failure"
    assert "credentials are expired or invalid" in result["summary"].lower()
    assert "refresh authentication tokens" in result["recommendation"].lower()
