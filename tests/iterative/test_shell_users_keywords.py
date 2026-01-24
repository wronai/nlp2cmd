import pytest

from nlp2cmd.generation.keywords import KeywordIntentDetector


class TestShellUserKeywords:
    @pytest.fixture
    def detector(self) -> KeywordIntentDetector:
        return KeywordIntentDetector()

    def test_shell_user_list_system_users_polish(self, detector: KeywordIntentDetector):
        result = detector.detect("Pokaż użytkowników systemu")
        assert result.domain == "shell"
        assert result.intent == "user_list"
