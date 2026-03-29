"""
Mudipu CLI - Command-line interface for trace analysis and management.
"""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

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
    """
    Mudipu - LLM instrumentation and analysis toolkit.
    
    Analyze, visualize, and optimize your AI agent traces.
    Track token usage, detect inefficiencies, and measure context health.
    """
    pass


@cli.command()
@click.argument("trace_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format", "-f", 
    type=click.Choice(["text", "markdown"]), 
    default="text", 
    help="Output format: text for terminal, markdown for docs."
)
@click.option(
    "--output", "-o", 
    type=click.Path(path_type=Path), 
    help="Save summary to file instead of printing to console."
)
def analyze(trace_file: Path, format: str, output: Path | None) -> None:
    """
    Generate a human-readable summary of a trace.
    
    Displays high-level overview including turn count, duration,
    token usage, and key events in the agent's execution.
    
    Example:
        mudipu analyze trace.json --format markdown -o summary.md
    """
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
    """
    Display detailed statistics and metrics for a trace.
    
    Shows comprehensive breakdown including:
    - Token usage (prompt, completion, total)
    - Model distribution across turns
    - Tool usage frequency
    - Cost estimates per model
    - Duration statistics
    
    Example:
        mudipu stats trace.json
    """
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
@click.option(
    "--goal", "-g", 
    type=str, 
    help="User's goal/objective for relevance scoring. If not provided, uses session metadata."
)
@click.option(
    "--visualize", "-v", 
    is_flag=True, 
    help="Generate matplotlib visualization chart with health trends and breakdowns."
)
@click.option(
    "--output-dir", "-o", 
    type=click.Path(path_type=Path), 
    help="Output directory for visualization (default: current directory)."
)
@click.option(
    "--save-json", "-s", 
    type=click.Path(path_type=Path), 
    help="Save complete health metrics to JSON file for further analysis."
)
@click.option(
    "--threshold", "-t", 
    type=float, 
    default=0.5, 
    help="Health score threshold for warnings (default: 0.5). Scores below this trigger alerts."
)
def health(
    trace_file: Path,
    goal: str | None,
    visualize: bool,
    output_dir: Path | None,
    save_json: Path | None,
    threshold: float
) -> None:
    """
    Analyze context health metrics for agent traces.
    
    Computes quality metrics including:
    - Relevance: How on-topic is the context?
    - Redundancy: Repeated/duplicate content detection
    - Saturation: Context window pressure analysis
    - Tool Loops: Inefficient repeated tool calls
    - Novelty: Progress tracking across turns
    - Drift: Goal alignment over time
    
    Outputs per-turn and session-level health scores with color-coded warnings.
    
    Example:
        mudipu health trace.json --visualize --threshold 0.6
    """
    try:
        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # Task for tracking progress
            task = progress.add_task("[cyan]Loading trace file...", total=None)
            
            # Load trace
            exporter = JSONExporter()
            session = exporter.load(trace_file)
            
            # Check if health extras are installed
            try:
                progress.update(task, description="[cyan]Initializing analyzer...")
                analyzer = TraceAnalyzer(session)
                
                # Create progress callback
                def update_progress(message: str):
                    progress.update(task, description=f"[cyan]{message}")
                
                # Run analysis with progress updates
                progress.update(task, description="[cyan]Computing health metrics...")
                metrics = analyzer.get_health_metrics(
                    goal=goal,
                    include_viz=visualize,
                    output_dir=output_dir,
                    progress_callback=update_progress
                )
                
                progress.update(task, description="[green]✓ Analysis complete!")
                
            except ImportError as e:
                progress.stop()
                console.print(f"[red]Error:[/red] {e}")
                console.print("\n[yellow]Install health dependencies:[/yellow]")
                console.print("  pip install mudipu[health]")
                raise click.Abort()
        
        # Display header
        console.print(Panel(
            f"[bold]{session.name or 'Trace Session'}[/bold]\n"
            f"Health Analysis",
            style="cyan"
        ))
        
        # Per-turn metrics table
        turn_table = Table(title="Turn Health Metrics", show_header=True)
        turn_table.add_column("Turn", style="cyan", justify="center")
        turn_table.add_column("Health", style="bold", justify="right")
        turn_table.add_column("Relevance", justify="right")
        turn_table.add_column("Duplicate", justify="right")
        turn_table.add_column("Saturation", justify="right")
        turn_table.add_column("Tool Loop", justify="right")
        turn_table.add_column("Novelty", justify="right")
        
        for turn_metric in metrics["per_turn"]:
            # Color-code health score
            health = turn_metric["health_score"]
            if health >= 0.7:
                health_str = f"[green]{health:.3f}[/green]"
            elif health >= threshold:
                health_str = f"[yellow]{health:.3f}[/yellow]"
            else:
                health_str = f"[red]{health:.3f}[/red]"
            
            turn_table.add_row(
                str(turn_metric["turn_number"]),
                health_str,
                f"{turn_metric['relevance_score']:.3f}",
                f"{turn_metric['duplicate_ratio']:.3f}",
                f"{turn_metric['saturation_score']:.3f}",
                f"{turn_metric['tool_loop_score']:.3f}",
                f"{turn_metric['novelty_score']:.3f}",
            )
        
        console.print(turn_table)
        
        # Session summary table
        session_metrics = metrics["session"]
        summary_table = Table(title="Session Summary", show_header=True)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Score", style="bold", justify="right")
        summary_table.add_column("Interpretation", style="dim")
        
        def interpret_score(score: float, reverse: bool = False) -> tuple[str, str]:
            """Color-code and interpret a score."""
            if reverse:
                score = 1 - score
            
            if score >= 0.7:
                return f"[green]{score:.3f}[/green]", "Healthy"
            elif score >= threshold:
                return f"[yellow]{score:.3f}[/yellow]", "Moderate"
            else:
                return f"[red]{score:.3f}[/red]", "Unhealthy"
        
        overall_score, overall_interp = interpret_score(session_metrics["overall_health"])
        summary_table.add_row("[bold]Overall Health[/bold]", f"[bold]{overall_score}[/bold]", f"[bold]{overall_interp}[/bold]")
        
        progress_score, progress_interp = interpret_score(session_metrics["progress_score"])
        summary_table.add_row("Progress", progress_score, progress_interp)
        
        effectiveness_score, effectiveness_interp = interpret_score(session_metrics["effectiveness_score"])
        summary_table.add_row("Effectiveness", effectiveness_score, effectiveness_interp)
        
        # Reverse interpretation for drift and loop (lower is better)
        drift_score, drift_interp = interpret_score(session_metrics["drift_score"], reverse=True)
        summary_table.add_row("Anti-Drift", drift_score, drift_interp)
        
        loop_score, loop_interp = interpret_score(session_metrics["loop_score"], reverse=True)
        summary_table.add_row("Anti-Loop", loop_score, loop_interp)
        
        growth_rate = session_metrics["context_growth_rate"]
        growth_color = "green" if 0 < growth_rate < 100 else "yellow" if growth_rate < 200 else "red"
        summary_table.add_row(
            "Context Growth Rate",
            f"[{growth_color}]{growth_rate:.1f}[/{growth_color}]",
            f"tokens/turn"
        )
        
        console.print(summary_table)
        
        # Display visualization path if generated
        if "visualization_path" in metrics:
            console.print(f"\n[green]✓[/green] Visualization saved to {metrics['visualization_path']}")
        
        # Save JSON if requested
        if save_json:
            import json
            with open(save_json, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            console.print(f"[green]✓[/green] Metrics saved to {save_json}")
        
        # Display warnings/insights from session details
        if session_metrics.get("details"):
            insights = []
            details = session_metrics["details"]
            
            if details.get("has_loops"):
                insights.append("[yellow]⚠[/yellow] Tool loops detected")
            
            if session_metrics["drift_score"] > 0.3:
                insights.append("[yellow]⚠[/yellow] Significant goal drift detected")
            
            if session_metrics["context_growth_rate"] > 200:
                insights.append("[red]⚠[/red] Rapid context growth (risk of saturation)")
            
            if session_metrics["effectiveness_score"] < threshold:
                insights.append(f"[red]⚠[/red] Low effectiveness (below {threshold:.2f} threshold)")
            
            if session_metrics["overall_health"] < threshold:
                insights.append(f"[red]⚠[/red] Overall health below threshold ({threshold:.2f})")
            
            if insights:
                console.print(Panel("\n".join(insights), title="Insights", style="yellow"))
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.argument("trace_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o", 
    type=click.Path(path_type=Path), 
    help="Custom output path for HTML file (default: auto-generated)."
)
def export_html(trace_file: Path, output: Path | None) -> None:
    """
    Export trace to interactive HTML report.
    
    Creates a self-contained HTML file with formatted trace data,
    collapsible sections, and syntax highlighting. Perfect for
    sharing or archiving agent runs.
    
    Example:
        mudipu export-html trace.json -o report.html
    """
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
    """
    List all trace files in a directory.
    
    Scans for JSON trace files and displays them in a table
    with file size and modification time.
    
    Example:
        mudipu list-traces ./traces
    """
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
    """
    Manage Mudipu configuration settings.
    
    Configure trace directory, export behavior, platform integration,
    and other SDK settings via YAML config files.
    """
    pass


@config.command("show")
def config_show() -> None:
    """
    Display current configuration settings.
    
    Shows all active settings including trace directory,
    export format, platform URL, and debug mode.
    
    Example:
        mudipu config show
    """
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
    """
    Initialize a new configuration file.
    
    Creates a mudipu.yaml file with default settings that you can edit.
    
    Example:
        mudipu config init
        mudipu config init custom-config.yaml
    """
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
    """
    Display Mudipu SDK version information.
    
    Example:
        mudipu version
    """
    console.print(f"[bold]Mudipu SDK[/bold] version [cyan]{__version__}[/cyan]")


if __name__ == "__main__":
    cli()
