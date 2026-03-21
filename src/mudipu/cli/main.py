"""
Mudipu CLI - Command-line interface for trace analysis and management.
"""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from mudipu.version import __version__
from mudipu.config import MudipuConfig, get_config, set_config
from mudipu.exporters.json_exporter import JSONExporter
from mudipu.exporters.html_exporter import HTMLExporter
from mudipu.analyzer.analyzer import TraceAnalyzer
from mudipu.analyzer.summary import SummaryGenerator

console = Console()


@click.group()
@click.version_option(__version__, "-v", "-V", "--version", prog_name="mudipu")
def cli() -> None:
    """Mudipu - LLM instrumentation and analysis toolkit."""
    pass


@cli.command()
@click.argument("trace_file", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "-f", type=click.Choice(["text", "markdown"]), default="text", help="Output format")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Save summary to file")
def analyze(trace_file: Path, format: str, output: Path | None) -> None:
    """Analyze a trace file and display summary."""
    try:
        # Load trace
        exporter = JSONExporter()
        session = exporter.load(trace_file)
        
        # Generate summary
        summary_gen = SummaryGenerator(session)
        
        if format == "markdown":
            summary = summary_gen.generate_markdown_summary()
        else:
            summary = summary_gen.generate_text_summary()
        
        # Output
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(summary)
            console.print(f"[green]✓[/green] Summary saved to {output}")
        else:
            console.print(summary)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("trace_file", type=click.Path(exists=True, path_type=Path))
def stats(trace_file: Path) -> None:
    """Display detailed statistics for a trace."""
    try:
        # Load trace
        exporter = JSONExporter()
        session = exporter.load(trace_file)
        
        # Analyze
        analyzer = TraceAnalyzer(session)
        statistics = analyzer.get_statistics()
        
        # Display with Rich
        console.print(Panel(f"[bold]{session.name or 'Trace Session'}[/bold]", style="cyan"))
        
        # Basic stats table
        table = Table(title="Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Session ID", str(session.session_id))
        table.add_row("Turn Count", str(statistics["turn_count"]))
        table.add_row("Total Duration", f"{statistics['total_duration_ms']:.2f} ms")
        table.add_row("Average Duration", f"{statistics['avg_duration_ms']:.2f} ms")
        table.add_row("Total Tokens", f"{statistics['total_tokens']:,}")
        table.add_row("Average Tokens/Turn", f"{statistics['avg_tokens_per_turn']:.1f}")
        
        console.print(table)
        
        # Model usage
        if statistics["model_usage"]:
            model_table = Table(title="Model Usage", show_header=True)
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Turns", style="green")
            
            for model, count in statistics["model_usage"].items():
                model_table.add_row(model, str(count))
            
            console.print(model_table)
        
        # Tool usage
        if statistics["tool_usage"]:
            tool_table = Table(title="Tool Usage", show_header=True)
            tool_table.add_column("Tool", style="cyan")
            tool_table.add_column("Calls", style="green")
            
            for tool, count in statistics["tool_usage"].items():
                tool_table.add_row(tool, str(count))
            
            console.print(tool_table)
        
        # Cost estimate
        costs = analyzer.get_cost_estimate()
        if costs:
            cost_table = Table(title="Estimated Cost", show_header=True)
            cost_table.add_column("Model", style="cyan")
            cost_table.add_column("Cost (USD)", style="green")
            
            for model, cost in costs.items():
                if model != "total":
                    cost_table.add_row(model, f"${cost:.4f}")
            
            cost_table.add_row("[bold]Total[/bold]", f"[bold]${costs.get('total', 0):.4f}[/bold]")
            
            console.print(cost_table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("trace_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output HTML file path")
def export_html(trace_file: Path, output: Path | None) -> None:
    """Export trace to HTML format."""
    try:
        # Load trace
        json_exporter = JSONExporter()
        session = json_exporter.load(trace_file)
        
        # Export to HTML
        html_exporter = HTMLExporter()
        if output:
            output_path = output
            html_content = html_exporter._render_html(session)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            output_path = html_exporter.export(session)
        
        console.print(f"[green]✓[/green] HTML exported to {output_path}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
def list_traces(directory: Path) -> None:
    """List all trace files in a directory."""
    try:
        trace_files = list(directory.glob("*.json"))
        
        if not trace_files:
            console.print(f"[yellow]No trace files found in {directory}[/yellow]")
            return
        
        table = Table(title=f"Traces in {directory}", show_header=True)
        table.add_column("Filename", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Modified", style="yellow")
        
        for trace_file in sorted(trace_files):
            stat = trace_file.stat()
            size_kb = stat.st_size / 1024
            modified = Path(trace_file).stat().st_mtime
            from datetime import datetime
            modified_str = datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M:%S")
            
            table.add_row(trace_file.name, f"{size_kb:.1f} KB", modified_str)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.group()
def config() -> None:
    """Manage Mudipu configuration."""
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    try:
        cfg = get_config()
        
        console.print(Panel("[bold]Mudipu Configuration[/bold]", style="cyan"))
        
        table = Table(show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Enabled", str(cfg.enabled))
        table.add_row("Trace Directory", str(cfg.trace_dir))
        table.add_row("Auto Export", str(cfg.auto_export))
        table.add_row("Export Format", cfg.export_format)
        table.add_row("Platform Enabled", str(cfg.platform_enabled))
        table.add_row("Platform URL", cfg.platform_url or "Not set")
        table.add_row("Debug", str(cfg.debug))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@config.command("init")
@click.argument("output", type=click.Path(path_type=Path), default=Path("mudipu.yaml"))
def config_init(output: Path) -> None:
    """Initialize a configuration file."""
    try:
        cfg = MudipuConfig()
        cfg.to_yaml(output)
        
        console.print(f"[green]✓[/green] Configuration file created at {output}")
        console.print("\nEdit this file to customize your Mudipu settings.")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
def version() -> None:
    """Display version information."""
    console.print(f"[bold]Mudipu SDK[/bold] version [cyan]{__version__}[/cyan]")


if __name__ == "__main__":
    cli()
