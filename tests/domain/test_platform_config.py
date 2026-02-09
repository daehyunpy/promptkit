"""Tests for PlatformConfig value object."""

import pytest

from promptkit.domain.platform_config import PlatformConfig
from promptkit.domain.platform_target import PlatformTarget


class TestPlatformConfig:
    def test_create_with_all_fields(self) -> None:
        config = PlatformConfig(
            name="cursor",
            platform_type=PlatformTarget.CURSOR,
            output_dir=".cursor",
        )
        assert config.name == "cursor"
        assert config.platform_type == PlatformTarget.CURSOR
        assert config.output_dir == ".cursor"

    def test_is_immutable(self) -> None:
        config = PlatformConfig(
            name="cursor",
            platform_type=PlatformTarget.CURSOR,
            output_dir=".cursor",
        )
        with pytest.raises(AttributeError):
            config.name = "other"  # type: ignore[misc]

    def test_equality_same_values(self) -> None:
        c1 = PlatformConfig(
            name="cursor",
            platform_type=PlatformTarget.CURSOR,
            output_dir=".cursor",
        )
        c2 = PlatformConfig(
            name="cursor",
            platform_type=PlatformTarget.CURSOR,
            output_dir=".cursor",
        )
        assert c1 == c2

    def test_claude_code_config(self) -> None:
        config = PlatformConfig(
            name="claude-code",
            platform_type=PlatformTarget.CLAUDE_CODE,
            output_dir=".claude",
        )
        assert config.name == "claude-code"
        assert config.platform_type == PlatformTarget.CLAUDE_CODE
        assert config.output_dir == ".claude"
