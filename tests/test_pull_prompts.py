"""
Testes unitários para src/pull_prompts.py.

hub.pull() é mockado - nenhuma chamada real ao LangSmith Hub é feita aqui.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pull_prompts


def _fake_message(template: str) -> MagicMock:
    """Cria um objeto fake com o mesmo shape de um *MessagePromptTemplate do LangChain."""
    message = MagicMock()
    message.prompt.template = template
    return message


class TestPullPrompts:
    def test_pull_prompts_from_langsmith_extracts_system_and_user_messages(self):
        fake_prompt = MagicMock()
        fake_prompt.messages = [
            _fake_message("Você é um assistente. Bug: {bug_report}"),
            _fake_message("{bug_report}"),
        ]

        with patch.object(pull_prompts.hub, "pull", return_value=fake_prompt) as mock_pull:
            result = pull_prompts.pull_prompts_from_langsmith()

        mock_pull.assert_called_once_with(pull_prompts.PROMPT_NAME)

        data = result["bug_to_user_story_v1"]
        assert data["system_prompt"] == "Você é um assistente. Bug: {bug_report}"
        assert data["user_prompt"] == "{bug_report}"
        assert data["version"] == "v1"
        assert isinstance(data["tags"], list) and len(data["tags"]) >= 1

    def test_pull_prompts_from_langsmith_propagates_hub_errors(self):
        with patch.object(pull_prompts.hub, "pull", side_effect=RuntimeError("prompt não encontrado")):
            try:
                pull_prompts.pull_prompts_from_langsmith()
                assert False, "esperava que a exceção do hub.pull fosse propagada"
            except RuntimeError as e:
                assert "não encontrado" in str(e)