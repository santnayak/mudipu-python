"""Analyzer module for trace analysis."""
from mudipu.analyzer.analyzer import TraceAnalyzer
from mudipu.analyzer.summary import SummaryGenerator

# Try to import health classes (optional dependencies)
try:
    from mudipu.analyzer.health import (
        ContextHealthAnalyzer,
        TurnHealthMetrics,
        SessionHealthMetrics,
        HealthAnalysis,
    )
    from mudipu.analyzer.visualizer import HealthVisualizer
    
    __all__ = [
        "TraceAnalyzer",
        "SummaryGenerator",
        "ContextHealthAnalyzer",
        "TurnHealthMetrics",
        "SessionHealthMetrics",
        "HealthAnalysis",
        "HealthVisualizer",
    ]
except ImportError:
    # Health extras not installed
    __all__ = [
        "TraceAnalyzer",
        "SummaryGenerator",
    ]
