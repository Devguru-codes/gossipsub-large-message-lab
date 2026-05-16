"""Command line interface for the research toolkit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from .protocol import LargeMessage, Segmenter
from .reports import result_to_json, result_to_markdown, write_report
from .security import matrix_to_markdown
from .simulator import SimulationConfig, Simulator

app = typer.Typer(
    help="Research toolkit for Gossipsub 1.4 large-message handling models.",
    no_args_is_help=True,
)


@app.command()
def segment(
    text: Annotated[Optional[str], typer.Option(help="UTF-8 text payload to segment.")] = None,
    file: Annotated[
        Optional[Path],
        typer.Option(exists=True, dir_okay=False, help="Payload file to segment."),
    ] = None,
    segment_size: Annotated[
        int,
        typer.Option(min=1, help="Maximum segment payload size in bytes."),
    ] = 1024,
    topic: Annotated[
        str,
        typer.Option(help="Topic name used for message ID derivation."),
    ] = "large-messages",
    publisher: Annotated[
        str,
        typer.Option(help="Publisher ID used for message ID derivation."),
    ] = "peer-0",
) -> None:
    """Inspect deterministic segmentation metadata for a payload."""
    payload = _read_payload(text, file)
    message = LargeMessage(topic=topic, publisher=publisher, payload=payload)
    segments = Segmenter(segment_size).segment(message)
    output = {
        "message_id": message.message_id,
        "message_hash": message.payload_hash,
        "payload_size": len(payload),
        "segment_size": segment_size,
        "segment_count": len(segments),
        "segments": [
            {
                "segment_id": item.segment_id,
                "index": item.index,
                "total": item.total,
                "size": len(item.payload),
                "segment_hash": item.segment_hash,
            }
            for item in segments
        ],
    }
    typer.echo(json.dumps(output, indent=2, sort_keys=True))


@app.command()
def simulate(
    config: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="JSON scenario config.")],
    output: Annotated[Optional[Path], typer.Option(help="Optional output path for the report.")] = None,
    markdown: Annotated[bool, typer.Option(help="Render Markdown instead of JSON.")] = False,
) -> None:
    """Run a deterministic propagation simulation from a JSON config."""
    data = json.loads(config.read_text(encoding="utf-8"))
    sim_config = SimulationConfig.from_dict(data)
    result = Simulator(sim_config).run()
    rendered = result_to_markdown(result) if markdown else result_to_json(result)
    if output:
        write_report(output, rendered)
        typer.echo(f"wrote {output}")
    else:
        typer.echo(rendered)


@app.command()
def report(
    config: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="JSON scenario config.")],
    output: Annotated[Path, typer.Option(help="Markdown report path.")] = Path(
        "reports/simulation-report.md"
    ),
) -> None:
    """Generate a Markdown simulation report."""
    data = json.loads(config.read_text(encoding="utf-8"))
    result = Simulator(SimulationConfig.from_dict(data)).run()
    write_report(output, result_to_markdown(result))
    typer.echo(f"wrote {output}")


@app.command("security-matrix")
def security_matrix(
    output: Annotated[Optional[Path], typer.Option(help="Optional Markdown output path.")] = None,
) -> None:
    """Emit the documented security threat matrix."""
    rendered = matrix_to_markdown()
    if output:
        write_report(output, rendered)
        typer.echo(f"wrote {output}")
    else:
        typer.echo(rendered)


def _read_payload(text: str | None, file: Path | None) -> bytes:
    if text is not None and file is not None:
        raise typer.BadParameter("provide either --text or --file, not both")
    if file is not None:
        return file.read_bytes()
    if text is not None:
        return text.encode("utf-8")
    return b""
