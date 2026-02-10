"""End-to-end integration tests for the init command."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from promptkit.cli import app
from promptkit.infra.config.yaml_loader import YamlLoader

runner = CliRunner()


@pytest.mark.integration
class TestInitEndToEnd:
    """Integration tests that verify init creates real files on disk."""

    def test_init_creates_all_expected_files_and_directories(
        self, project_dir: Path
    ) -> None:
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert (project_dir / "promptkit.yaml").exists()
        assert (project_dir / "promptkit.lock").exists()
        assert (project_dir / ".promptkit" / "cache").is_dir()
        assert (project_dir / "prompts").is_dir()
        assert (project_dir / ".cursor").is_dir()
        assert (project_dir / ".claude").is_dir()
        assert (project_dir / ".gitignore").exists()

    def test_init_generates_parseable_config(self, project_dir: Path) -> None:
        runner.invoke(app, ["init"])

        yaml_content = (project_dir / "promptkit.yaml").read_text()
        config = YamlLoader().load(yaml_content)

        assert len(config.platform_configs) >= 2
        assert len(config.registries) >= 1

    def test_init_fails_in_already_initialized_directory(
        self, project_dir: Path
    ) -> None:
        (project_dir / "promptkit.yaml").write_text("version: 1")

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "already exists" in result.output
