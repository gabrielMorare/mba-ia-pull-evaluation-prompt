"""
Testes unitários para src/push_prompts.py.

O Client do LangSmith é mockado - nenhum push real acontece aqui.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import push_prompts

SAMPLE_PROMPT_DATA = {
    "description": "Descrição de teste",
    "system_prompt": "Você é um Product Manager. {bug_report}",
    "user_prompt": "{bug_report}",
    "version": "v2",
    "tags": ["bug-analysis"],
    "techniques_applied": ["Few-shot Learning", "Role Prompting"],
}


class TestPushPrompts:
    def test_push_prompt_builds_chat_template_and_calls_client_as_public(self):
        mock_client_instance = MagicMock()
        mock_client_instance.push_prompt.return_value = (
            "https://smith.langchain.com/prompts/user/bug_to_user_story_v2"
        )

        with patch.object(push_prompts, "Client", return_value=mock_client_instance) as mock_client_cls:
            result = push_prompts.push_prompt_to_langsmith(
                "gabrielmorare/bug_to_user_story_v2", SAMPLE_PROMPT_DATA
            )

        assert result is True
        mock_client_cls.assert_called_once()

        call_args = mock_client_instance.push_prompt.call_args
        assert call_args.args[0] == "gabrielmorare/bug_to_user_story_v2"

        kwargs = call_args.kwargs
        assert kwargs["is_public"] is True
        assert kwargs["description"] == SAMPLE_PROMPT_DATA["description"]
        assert set(kwargs["tags"]) == {"Few-shot Learning", "Role Prompting", "bug-analysis"}

        prompt_template = kwargs["object"]
        assert prompt_template.messages[0].prompt.template == SAMPLE_PROMPT_DATA["system_prompt"]
        assert prompt_template.messages[1].prompt.template == SAMPLE_PROMPT_DATA["user_prompt"]

    def test_push_prompt_returns_false_on_client_error(self):
        mock_client_instance = MagicMock()
        mock_client_instance.push_prompt.side_effect = RuntimeError("falha simulada")

        with patch.object(push_prompts, "Client", return_value=mock_client_instance):
            result = push_prompts.push_prompt_to_langsmith(
                "gabrielmorare/bug_to_user_story_v2", SAMPLE_PROMPT_DATA
            )

        assert result is False
