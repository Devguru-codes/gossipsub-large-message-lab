from pathlib import Path

from typer.testing import CliRunner

from gossipsub_large_msg_lab.cli import app

runner = CliRunner()


def test_segment_command_outputs_metadata() -> None:
    result = runner.invoke(app, ["segment", "--text", "abcdef", "--segment-size", "3"])

    assert result.exit_code == 0
    assert '"segment_count": 2' in result.stdout


def test_simulate_command_outputs_json() -> None:
    result = runner.invoke(app, ["simulate", "examples/basic-scenario.json"])

    assert result.exit_code == 0
    assert '"completion_rate"' in result.stdout


def test_report_command_writes_markdown(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    result = runner.invoke(app, ["report", "examples/basic-scenario.json", "--output", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "Simulation Report" in output.read_text(encoding="utf-8")


def test_security_matrix_command_outputs_markdown() -> None:
    result = runner.invoke(app, ["security-matrix"])

    assert result.exit_code == 0
    assert "Security Matrix" in result.stdout
