"""Tests for PlatformTarget enum."""

from promptkit.domain.platform_target import PlatformTarget


class TestPlatformTarget:
    def test_cursor_variant_exists(self) -> None:
        assert PlatformTarget.CURSOR is not None

    def test_claude_code_variant_exists(self) -> None:
        assert PlatformTarget.CLAUDE_CODE is not None

    def test_cursor_value(self) -> None:
        assert PlatformTarget.CURSOR.value == "cursor"

    def test_claude_code_value(self) -> None:
        assert PlatformTarget.CLAUDE_CODE.value == "claude-code"

    def test_from_string_cursor(self) -> None:
        assert PlatformTarget.from_string("cursor") == PlatformTarget.CURSOR

    def test_from_string_claude_code(self) -> None:
        assert PlatformTarget.from_string("claude-code") == PlatformTarget.CLAUDE_CODE

    def test_from_string_invalid_raises(self) -> None:
        try:
            PlatformTarget.from_string("invalid")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "invalid" in str(e)

    def test_all_platforms_returns_both(self) -> None:
        all_platforms = list(PlatformTarget)
        assert len(all_platforms) == 2
        assert PlatformTarget.CURSOR in all_platforms
        assert PlatformTarget.CLAUDE_CODE in all_platforms
