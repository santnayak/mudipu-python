"""
Example showing analysis of traces.
"""

from pathlib import Path
from mudipu.exporters import JSONExporter
from mudipu.analyzer import TraceAnalyzer, SummaryGenerator


def main():
    """Analyze trace files."""
    # Find trace files
    trace_dir = Path(".mudipu/traces")

    if not trace_dir.exists():
        print("No trace directory found. Run basic_example.py first to generate traces.")
        return

    trace_files = list(trace_dir.glob("*.json"))

    if not trace_files:
        print("No trace files found. Run basic_example.py first to generate traces.")
        return

    # Load and analyze the latest trace
    latest_trace = sorted(trace_files, key=lambda p: p.stat().st_mtime)[-1]
    print(f"Analyzing: {latest_trace.name}\n")

    # Load the session
    exporter = JSONExporter()
    session = exporter.load(latest_trace)

    # Create analyzer
    analyzer = TraceAnalyzer(session)

    # Get statistics
    stats = analyzer.get_statistics()

    print("=== Basic Statistics ===")
    print(f"Session: {session.name}")
    print(f"Turns: {stats['turn_count']}")
    print(f"Total Tokens: {stats['total_tokens']:,}")
    print(f"Average Duration: {stats['avg_duration_ms']:.2f}ms")
    print()

    # Model usage
    print("=== Model Usage ===")
    for model, count in stats["model_usage"].items():
        print(f"  {model}: {count} turns")
    print()

    # Cost estimate
    print("=== Cost Estimate ===")
    costs = analyzer.get_cost_estimate()
    for model, cost in costs.items():
        if model != "total":
            print(f"  {model}: ${cost:.4f}")
    print(f"  Total: ${costs.get('total', 0):.4f}")
    print()

    # Generate text summary
    print("=== Full Summary ===")
    summary_gen = SummaryGenerator(session)
    print(summary_gen.generate_text_summary())

    # Find slow turns
    slow_turns = analyzer.find_slow_turns(threshold_ms=500)
    if slow_turns:
        print("\n=== Slow Turns (>500ms) ===")
        for turn in slow_turns:
            print(f"  Turn {turn.turn_number}: {turn.duration_ms:.2f}ms")


if __name__ == "__main__":
    main()
