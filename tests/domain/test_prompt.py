"""Tests for Prompt aggregate root."""

import hashlib

from promptkit.domain.platform_target import PlatformTarget
from promptkit.domain.prompt import Prompt
from promptkit.domain.prompt_metadata import PromptMetadata
from promptkit.domain.prompt_spec import PromptSpec


class TestPromptCreation:
    def test_create_from_spec_and_content(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/code-review")
        prompt = Prompt(spec=spec, content="You are a code reviewer.")
        assert prompt.spec is spec
        assert prompt.content == "You are a code reviewer."
        assert prompt.metadata is None

    def test_create_with_metadata(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/code-review")
        metadata = PromptMetadata(author="Anthropic", version="1.0.0")
        prompt = Prompt(spec=spec, content="content", metadata=metadata)
        assert prompt.metadata == metadata

    def test_name_delegates_to_spec(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/code-review")
        prompt = Prompt(spec=spec, content="content")
        assert prompt.name == "code-review"

    def test_source_delegates_to_spec(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/code-review")
        prompt = Prompt(spec=spec, content="content")
        assert prompt.source == "claude-plugins-official/code-review"


class TestPromptContentHash:
    def test_content_hash_is_sha256(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/test")
        prompt = Prompt(spec=spec, content="hello world")
        expected = "sha256:" + hashlib.sha256(b"hello world").hexdigest()
        assert prompt.content_hash == expected

    def test_content_hash_deterministic(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/test")
        p1 = Prompt(spec=spec, content="same content")
        p2 = Prompt(spec=spec, content="same content")
        assert p1.content_hash == p2.content_hash

    def test_content_hash_changes_with_content(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/test")
        p1 = Prompt(spec=spec, content="content A")
        p2 = Prompt(spec=spec, content="content B")
        assert p1.content_hash != p2.content_hash


class TestPromptPlatformTargeting:
    def test_is_valid_for_platform_when_targeted(self) -> None:
        spec = PromptSpec(
            source="claude-plugins-official/test",
            platforms=(PlatformTarget.CURSOR,),
        )
        prompt = Prompt(spec=spec, content="content")
        assert prompt.is_valid_for_platform(PlatformTarget.CURSOR) is True

    def test_is_not_valid_for_platform_when_excluded(self) -> None:
        spec = PromptSpec(
            source="claude-plugins-official/test",
            platforms=(PlatformTarget.CURSOR,),
        )
        prompt = Prompt(spec=spec, content="content")
        assert prompt.is_valid_for_platform(PlatformTarget.CLAUDE_CODE) is False

    def test_is_valid_for_all_platforms_when_none_specified(self) -> None:
        spec = PromptSpec(source="claude-plugins-official/test")
        prompt = Prompt(spec=spec, content="content")
        assert prompt.is_valid_for_platform(PlatformTarget.CURSOR) is True
        assert prompt.is_valid_for_platform(PlatformTarget.CLAUDE_CODE) is True
