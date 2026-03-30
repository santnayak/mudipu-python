"""
Comprehensive tests for context health metrics.

Tests all per-turn and session-level health metrics.
"""

import pytest
import numpy as np
from mudipu.models import Session, BaseTurn, ToolCall
from mudipu.analyzer.health import ContextHealthAnalyzer, TurnHealthMetrics, SessionHealthMetrics, HealthAnalysis


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    turns = [
        BaseTurn(
            turn_number=1,
            request_messages=[{"role": "user", "content": "What is the weather in Paris?"}],
            response_message={"role": "assistant", "content": "I'll check the weather for you."},
            tool_calls_detected=[],
            usage={"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
            duration_ms=500,
            model="gpt-4",
        ),
        BaseTurn(
            turn_number=2,
            request_messages=[
                {"role": "user", "content": "What is the weather in Paris?"},
                {"role": "assistant", "content": "I'll check the weather for you."},
            ],
            response_message={"role": "assistant", "content": "The weather in Paris is sunny, 22°C."},
            tool_calls_detected=[ToolCall(function_name="get_weather", arguments={"city": "Paris"})],
            usage={"prompt_tokens": 150, "completion_tokens": 15, "total_tokens": 165},
            duration_ms=800,
            model="gpt-4",
        ),
    ]

    return Session(
        session_id="test-session-123",
        trace_id="test-trace-123",
        name="test-session",
        turns=turns,
        turn_count=2,
        total_tokens=275,
        total_duration_ms=1300,
        metadata={"user_input": "What is the weather in Paris?"},
    )


@pytest.fixture
def looping_session():
    """Create a session with tool loops."""
    turns = [
        BaseTurn(
            turn_number=1,
            request_messages=[{"role": "user", "content": "Find info about Python"}],
            response_message={"role": "assistant", "content": "Searching..."},
            tool_calls_detected=[ToolCall(function_name="web_search", arguments={"query": "Python"})],
            usage={"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
            duration_ms=500,
            model="gpt-4",
        ),
        BaseTurn(
            turn_number=2,
            request_messages=[{"role": "user", "content": "Find info about Python"}],
            response_message={"role": "assistant", "content": "Searching again..."},
            tool_calls_detected=[ToolCall(function_name="web_search", arguments={"query": "Python"})],
            usage={"prompt_tokens": 200, "completion_tokens": 10, "total_tokens": 210},
            duration_ms=500,
            model="gpt-4",
        ),
        BaseTurn(
            turn_number=3,
            request_messages=[{"role": "user", "content": "Find info about Python"}],
            response_message={"role": "assistant", "content": "Searching once more..."},
            tool_calls_detected=[ToolCall(function_name="web_search", arguments={"query": "Python"})],
            usage={"prompt_tokens": 300, "completion_tokens": 10, "total_tokens": 310},
            duration_ms=500,
            model="gpt-4",
        ),
    ]

    return Session(
        session_id="loop-session-123",
        trace_id="loop-trace-123",
        name="loop-session",
        turns=turns,
        turn_count=3,
        total_tokens=630,
        total_duration_ms=1500,
        metadata={"user_input": "Find info about Python"},
    )


class TestContextHealthAnalyzer:
    """Test ContextHealthAnalyzer initialization and basic functionality."""

    def test_initialization(self, sample_session):
        """Test analyzer initialization."""
        analyzer = ContextHealthAnalyzer(sample_session)

        assert analyzer.session == sample_session
        assert analyzer.assumed_context_limit == 8192
        assert analyzer.goal == "What is the weather in Paris?"

    def test_initialization_with_custom_goal(self, sample_session):
        """Test initialization with custom goal."""
        analyzer = ContextHealthAnalyzer(sample_session, goal="Custom goal here")

        assert analyzer.goal == "Custom goal here"

    def test_initialization_with_custom_limit(self, sample_session):
        """Test initialization with custom context limit."""
        analyzer = ContextHealthAnalyzer(sample_session, assumed_context_limit=128000)

        assert analyzer.assumed_context_limit == 128000

    def test_progress_callback(self, sample_session):
        """Test progress callback functionality."""
        messages = []

        def callback(msg: str):
            messages.append(msg)

        analyzer = ContextHealthAnalyzer(sample_session, progress_callback=callback)

        # Trigger model loading
        _ = analyzer.model

        assert len(messages) > 0
        assert "Loading sentence transformer model" in messages[0]


class TestPerTurnMetrics:
    """Test per-turn health metrics computation."""

    def test_relevance_score(self, sample_session):
        """Test relevance score computation."""
        analyzer = ContextHealthAnalyzer(sample_session)
        metrics = analyzer.analyze_turn(0)

        assert isinstance(metrics.relevance_score, float)
        assert 0.0 <= metrics.relevance_score <= 1.0
        # First turn should be highly relevant to goal
        assert metrics.relevance_score > 0.5

    def test_duplicate_ratio(self, sample_session):
        """Test duplicate ratio computation."""
        analyzer = ContextHealthAnalyzer(sample_session)
        metrics = analyzer.analyze_turn(0)

        assert isinstance(metrics.duplicate_ratio, float)
        assert 0.0 <= metrics.duplicate_ratio <= 1.0

    def test_saturation_score(self, sample_session):
        """Test saturation score computation."""
        analyzer = ContextHealthAnalyzer(sample_session)
        metrics = analyzer.analyze_turn(0)

        assert isinstance(metrics.saturation_score, float)
        assert 0.0 <= metrics.saturation_score <= 1.0
        # 100 tokens / 8192 limit = low saturation
        assert metrics.saturation_score < 0.2

    def test_tool_loop_score_first_turn(self, sample_session):
        """Test tool loop score for first turn (should be 0)."""
        analyzer = ContextHealthAnalyzer(sample_session)
        metrics = analyzer.analyze_turn(0)

        assert metrics.tool_loop_score == 0.0

    def test_tool_loop_detection(self, looping_session):
        """Test tool loop detection across multiple turns."""
        analyzer = ContextHealthAnalyzer(looping_session)

        # Turn 1: No loop (first turn)
        metrics_1 = analyzer.analyze_turn(0)
        assert metrics_1.tool_loop_score == 0.0

        # Turn 2: Should detect loop
        metrics_2 = analyzer.analyze_turn(1)
        assert metrics_2.tool_loop_score > 0.0

        # Turn 3: Loop intensifies
        metrics_3 = analyzer.analyze_turn(2)
        assert metrics_3.tool_loop_score > metrics_2.tool_loop_score

    def test_novelty_score_first_turn(self, sample_session):
        """Test novelty score for first turn (should be 1.0)."""
        analyzer = ContextHealthAnalyzer(sample_session)
        metrics = analyzer.analyze_turn(0)

        assert metrics.novelty_score == 1.0

    def test_novelty_score_subsequent_turns(self, sample_session):
        """Test novelty score for subsequent turns."""
        analyzer = ContextHealthAnalyzer(sample_session)
        metrics = analyzer.analyze_turn(1)

        assert isinstance(metrics.novelty_score, float)
        assert 0.0 <= metrics.novelty_score <= 1.0

    def test_health_score_combined(self, sample_session):
        """Test combined health score."""
        analyzer = ContextHealthAnalyzer(sample_session)
        metrics = analyzer.analyze_turn(0)

        assert isinstance(metrics.health_score, float)
        assert 0.0 <= metrics.health_score <= 1.0

        # Health score should be weighted combination
        expected = (
            0.3 * metrics.relevance_score
            + 0.2 * (1 - metrics.duplicate_ratio)
            + 0.1 * (1 - metrics.saturation_score)
            + 0.2 * (1 - metrics.tool_loop_score)
            + 0.2 * metrics.novelty_score
        )
        assert abs(metrics.health_score - expected) < 0.01


class TestSessionMetrics:
    """Test session-level health metrics."""

    def test_context_growth_rate(self, sample_session):
        """Test context growth rate computation."""
        analyzer = ContextHealthAnalyzer(sample_session)
        turn_metrics = [analyzer.analyze_turn(i) for i in range(2)]
        session_metrics = analyzer.analyze_session(turn_metrics)

        assert isinstance(session_metrics.context_growth_rate, float)
        # Growth: 100 → 150 = +50 tokens/turn
        assert session_metrics.context_growth_rate > 0

    def test_drift_score(self, sample_session):
        """Test drift score computation."""
        analyzer = ContextHealthAnalyzer(sample_session)
        turn_metrics = [analyzer.analyze_turn(i) for i in range(2)]
        session_metrics = analyzer.analyze_session(turn_metrics)

        assert isinstance(session_metrics.drift_score, float)
        assert 0.0 <= session_metrics.drift_score <= 1.0

    def test_loop_score(self, looping_session):
        """Test session loop score on looping session."""
        analyzer = ContextHealthAnalyzer(looping_session)
        turn_metrics = [analyzer.analyze_turn(i) for i in range(3)]
        session_metrics = analyzer.analyze_session(turn_metrics)

        assert isinstance(session_metrics.loop_score, float)
        assert 0.0 <= session_metrics.loop_score <= 1.0
        # Should detect loops
        assert session_metrics.loop_score > 0.3

    def test_progress_score(self, sample_session):
        """Test progress score computation."""
        analyzer = ContextHealthAnalyzer(sample_session)
        turn_metrics = [analyzer.analyze_turn(i) for i in range(2)]
        session_metrics = analyzer.analyze_session(turn_metrics)

        assert isinstance(session_metrics.progress_score, float)
        assert 0.0 <= session_metrics.progress_score <= 1.0

    def test_effectiveness_score(self, sample_session):
        """Test effectiveness score computation."""
        analyzer = ContextHealthAnalyzer(sample_session)
        turn_metrics = [analyzer.analyze_turn(i) for i in range(2)]
        session_metrics = analyzer.analyze_session(turn_metrics)

        assert isinstance(session_metrics.effectiveness_score, float)
        assert 0.0 <= session_metrics.effectiveness_score <= 1.0
        # Last turn has content, so effectiveness > 0
        assert session_metrics.effectiveness_score > 0.0

    def test_overall_health(self, sample_session):
        """Test overall health score."""
        analyzer = ContextHealthAnalyzer(sample_session)
        turn_metrics = [analyzer.analyze_turn(i) for i in range(2)]
        session_metrics = analyzer.analyze_session(turn_metrics)

        assert isinstance(session_metrics.overall_health, float)
        assert 0.0 <= session_metrics.overall_health <= 1.0


class TestFullAnalysis:
    """Test complete health analysis workflow."""

    def test_get_full_analysis(self, sample_session):
        """Test full analysis returns correct structure."""
        analyzer = ContextHealthAnalyzer(sample_session)
        analysis = analyzer.get_full_analysis()

        assert isinstance(analysis, HealthAnalysis)
        assert len(analysis.per_turn) == 2
        assert isinstance(analysis.session, SessionHealthMetrics)

    def test_per_turn_metrics_structure(self, sample_session):
        """Test per-turn metrics have correct structure."""
        analyzer = ContextHealthAnalyzer(sample_session)
        analysis = analyzer.get_full_analysis()

        for turn_metric in analysis.per_turn:
            assert isinstance(turn_metric, TurnHealthMetrics)
            assert hasattr(turn_metric, "turn_number")
            assert hasattr(turn_metric, "relevance_score")
            assert hasattr(turn_metric, "duplicate_ratio")
            assert hasattr(turn_metric, "saturation_score")
            assert hasattr(turn_metric, "tool_loop_score")
            assert hasattr(turn_metric, "novelty_score")
            assert hasattr(turn_metric, "health_score")
            assert hasattr(turn_metric, "details")

    def test_session_metrics_structure(self, sample_session):
        """Test session metrics have correct structure."""
        analyzer = ContextHealthAnalyzer(sample_session)
        analysis = analyzer.get_full_analysis()

        session = analysis.session
        assert hasattr(session, "session_id")
        assert hasattr(session, "turns_analyzed")
        assert hasattr(session, "context_growth_rate")
        assert hasattr(session, "drift_score")
        assert hasattr(session, "loop_score")
        assert hasattr(session, "progress_score")
        assert hasattr(session, "effectiveness_score")
        assert hasattr(session, "overall_health")
        assert hasattr(session, "details")

    def test_to_dict_conversion(self, sample_session):
        """Test conversion to dictionary."""
        analyzer = ContextHealthAnalyzer(sample_session)
        analysis = analyzer.get_full_analysis()

        result_dict = analysis.to_dict()

        assert "per_turn" in result_dict
        assert "session" in result_dict
        assert isinstance(result_dict["per_turn"], list)
        assert isinstance(result_dict["session"], dict)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_session(self):
        """Test analyzer with empty session."""
        session = Session(
            session_id="empty",
            trace_id="empty",
            name="empty",
            turns=[],
            turn_count=0,
            total_tokens=0,
            total_duration_ms=0,
            metadata={},
        )

        analyzer = ContextHealthAnalyzer(session)
        analysis = analyzer.get_full_analysis()

        assert len(analysis.per_turn) == 0
        assert analysis.session.turns_analyzed == 0

    def test_no_goal_provided(self, sample_session):
        """Test analyzer with no goal."""
        session_no_goal = Session(
            session_id=sample_session.session_id,
            trace_id=sample_session.trace_id,
            name=sample_session.name,
            turns=sample_session.turns,
            turn_count=sample_session.turn_count,
            total_tokens=sample_session.total_tokens,
            total_duration_ms=sample_session.total_duration_ms,
            metadata={},  # No goal
        )

        analyzer = ContextHealthAnalyzer(session_no_goal)
        metrics = analyzer.analyze_turn(0)

        # Relevance should be 0 without goal
        assert metrics.relevance_score == 0.0

    def test_turn_without_usage(self):
        """Test turn without usage data."""
        turn = BaseTurn(
            turn_number=1,
            request_messages=[{"role": "user", "content": "test"}],
            response_message={"role": "assistant", "content": "response"},
            tool_calls_detected=[],
            usage=None,  # No usage data
            duration_ms=500,
            model="gpt-4",
        )

        session = Session(
            session_id="test",
            trace_id="test",
            name="test",
            turns=[turn],
            turn_count=1,
            total_tokens=0,
            total_duration_ms=500,
            metadata={},
        )

        analyzer = ContextHealthAnalyzer(session)
        metrics = analyzer.analyze_turn(0)

        # Saturation should be 0 without usage
        assert metrics.saturation_score == 0.0


class TestUtilityMethods:
    """Test utility methods."""

    def test_cosine_similarity_matrix(self):
        """Test cosine similarity matrix computation."""
        vectors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])

        sim_matrix = ContextHealthAnalyzer._cosine_similarity_matrix(vectors)

        assert sim_matrix.shape == (3, 3)
        # Vector with itself should be 1.0
        assert np.isclose(sim_matrix[0, 0], 1.0)
        assert np.isclose(sim_matrix[1, 1], 1.0)
        # Orthogonal vectors should be 0.0
        assert np.isclose(sim_matrix[0, 1], 0.0)
        # Identical vectors should be 1.0
        assert np.isclose(sim_matrix[0, 2], 1.0)

    def test_clip_01(self):
        """Test _clip_01 method."""
        assert ContextHealthAnalyzer._clip_01(-0.5) == 0.0
        assert ContextHealthAnalyzer._clip_01(0.5) == 0.5
        assert ContextHealthAnalyzer._clip_01(1.5) == 1.0
        assert ContextHealthAnalyzer._clip_01(0.0) == 0.0
        assert ContextHealthAnalyzer._clip_01(1.0) == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
