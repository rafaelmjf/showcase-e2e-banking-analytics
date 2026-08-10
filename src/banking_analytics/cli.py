"""Command-line entry point for the planning scaffold."""

import typer

app = typer.Typer(help="Brazilian banking analytics data tools.")


@app.command()
def status() -> None:
    """Show the current implementation status."""
    typer.echo("Planning scaffold ready; source profiling is the next work package.")


@app.command()
def about() -> None:
    """Describe the project domain."""
    typer.echo("Official BCB balance-sheet and macroeconomic analytics showcase.")


if __name__ == "__main__":
    app()
