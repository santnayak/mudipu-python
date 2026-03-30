"""
Tests for analyzer functionality.
"""

from mudipu.analyzer.analyzer import TraceAnalyzer


def test_analyzer_statistics(sample_session):
    """Test analyzer statistics generation."""
    analyzer = TraceAnalyzer(sample_session)
    stats = analyzer.get_statistics()

    assert stats["turn_count"] == 1
    assert stats["total_tokens"] == 15
    assert stats["avg_duration_ms"] == 250.0
    assert "gpt-4" in stats["model_usage"]


def test_cost_estimate(sample_session):
    """Test cost estimation."""
    analyzer = TraceAnalyzer(sample_session)
    costs = analyzer.get_cost_estimate()

    assert "total" in costs
    assert costs["total"] > 0


def test_find_slow_turns(sample_session):
    """Test finding slow turns."""
    analyzer = TraceAnalyzer(sample_session)

    # Should not find any (threshold is higher)
    slow_turns = analyzer.find_slow_turns(threshold_ms=1000.0)
    assert len(slow_turns) == 0

    # Should find one (threshold is lower)
    slow_turns = analyzer.find_slow_turns(threshold_ms=100.0)
    assert len(slow_turns) == 1
