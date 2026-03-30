"""
Tests for Mudipu decorators.

Tests @trace_session, @trace_llm, @trace_tool functionality.
"""

import pytest
from mudipu.decorators import trace_session, trace_llm, trace_tool
from mudipu.tracer import get_current_session, clear_context
from mudipu.context import session_context
import time


@pytest.fixture(autouse=True)
def reset_context():
    """Reset context before each test."""
    clear_context()
    yield
    clear_context()


class TestTraceSession:
    """Test @trace_session decorator."""

    def test_trace_session_basic(self):
        """Test basic session tracing."""

        @trace_session(name="test-session")
        def simple_function():
            return "done"

        result = simple_function()

        assert result == "done"
        # Session should be complete
        session = get_current_session()
        assert session is not None
        assert session.name == "test-session"

    def test_trace_session_with_metadata(self):
        """Test session with metadata."""

        @trace_session(name="test-session", metadata={"key": "value"})
        def simple_function():
            return "done"

        simple_function()
        session = get_current_session()

        assert session.metadata["key"] == "value"

    def test_trace_session_nested_calls(self):
        """Test session with nested function calls."""

        @trace_session(name="outer")
        def outer_function():
            inner_function()
            return "outer done"

        @trace_llm()
        def inner_function():
            return "inner done"

        result = outer_function()

        assert result == "outer done"
        session = get_current_session()
        assert session.name == "outer"

    def test_trace_session_exception_handling(self):
        """Test session tracing with exceptions."""

        @trace_session(name="error-session")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        # Session should still be recorded
        session = get_current_session()
        assert session is not None


class TestTraceLLM:
    """Test @trace_llm decorator."""

    def test_trace_llm_basic(self):
        """Test basic LLM tracing."""

        @trace_session(name="llm-session")
        def session_function():
            @trace_llm()
            def llm_call():
                return {"role": "assistant", "content": "Hello"}

            return llm_call()

        result = session_function()

        assert result["content"] == "Hello"
        session = get_current_session()
        assert session.turn_count >= 1

    def test_trace_llm_with_messages(self):
        """Test LLM tracing with explicit messages."""

        @trace_session(name="llm-session")
        def session_function():
            @trace_llm(request_messages=[{"role": "user", "content": "Hi"}])
            def llm_call():
                return {"role": "assistant", "content": "Hello"}

            return llm_call()

        session_function()
        session = get_current_session()

        assert session.turn_count == 1
        turn = session.turns[0]
        assert turn.request_messages[0]["content"] == "Hi"

    def test_trace_llm_with_usage(self):
        """Test LLM tracing with usage information."""

        @trace_session(name="llm-session")
        def session_function():
            @trace_llm(usage_info={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
            def llm_call():
                return {"role": "assistant", "content": "Response"}

            return llm_call()

        session_function()
        session = get_current_session()

        turn = session.turns[0]
        assert turn.usage["total_tokens"] == 15

    def test_trace_llm_multiple_turns(self):
        """Test multiple LLM calls in one session."""

        @trace_session(name="multi-turn")
        def session_function():
            @trace_llm()
            def first_call():
                return {"role": "assistant", "content": "First"}

            @trace_llm()
            def second_call():
                return {"role": "assistant", "content": "Second"}

            first_call()
            second_call()
            return "done"

        session_function()
        session = get_current_session()

        assert session.turn_count == 2
        assert session.turns[0].response_message["content"] == "First"
        assert session.turns[1].response_message["content"] == "Second"


class TestTraceTool:
    """Test @trace_tool decorator."""

    def test_trace_tool_basic(self):
        """Test basic tool tracing."""

        @trace_session(name="tool-session")
        def session_function():
            @trace_llm()
            def llm_with_tool():
                @trace_tool(name="get_weather")
                def get_weather(city: str):
                    return {"temp": 72, "city": city}

                result = get_weather("San Francisco")
                return {"role": "assistant", "content": f"Weather: {result}"}

            return llm_with_tool()

        session_function()
        session = get_current_session()

        turn = session.turns[0]
        assert len(turn.tool_calls_detected) >= 1
        tool_call = turn.tool_calls_detected[0]
        assert tool_call["name"] == "get_weather"

    def test_trace_tool_with_arguments(self):
        """Test tool tracing with arguments."""

        @trace_session(name="tool-session")
        def session_function():
            @trace_llm()
            def llm_with_tool():
                @trace_tool(name="calculate")
                def calculate(a: int, b: int):
                    return a + b

                result = calculate(5, 3)
                return {"role": "assistant", "content": str(result)}

            return llm_with_tool()

        session_function()
        session = get_current_session()

        tool_call = session.turns[0].tool_calls_detected[0]
        assert tool_call["arguments"]["a"] == 5
        assert tool_call["arguments"]["b"] == 3

    def test_trace_tool_multiple_calls(self):
        """Test multiple tool calls."""

        @trace_session(name="multi-tool")
        def session_function():
            @trace_llm()
            def llm_with_tools():
                @trace_tool(name="tool1")
                def tool1():
                    return "result1"

                @trace_tool(name="tool2")
                def tool2():
                    return "result2"

                tool1()
                tool2()
                return {"role": "assistant", "content": "Done"}

            return llm_with_tools()

        session_function()
        session = get_current_session()

        turn = session.turns[0]
        assert len(turn.tool_calls_detected) == 2
        assert turn.tool_calls_detected[0]["name"] == "tool1"
        assert turn.tool_calls_detected[1]["name"] == "tool2"


class TestNestedDecorators:
    """Test nested decorator scenarios."""

    def test_session_llm_tool_nesting(self):
        """Test full nesting: session -> LLM -> tool."""

        @trace_session(name="complex-session")
        def complex_workflow():
            @trace_llm()
            def llm_step1():
                @trace_tool(name="search")
                def search(query: str):
                    return f"Results for {query}"

                result = search("Python tutorial")
                return {"role": "assistant", "content": result}

            @trace_llm()
            def llm_step2():
                return {"role": "assistant", "content": "Summarized"}

            llm_step1()
            llm_step2()
            return "workflow complete"

        result = complex_workflow()

        assert result == "workflow complete"
        session = get_current_session()
        assert session.turn_count == 2
        assert len(session.turns[0].tool_calls_detected) >= 1


class TestContextManager:
    """Test context manager integration with decorators."""

    def test_decorator_with_context_manager(self):
        """Test using decorators within context manager."""
        with session_context(name="ctx-session") as session:

            @trace_llm()
            def llm_call():
                return {"role": "assistant", "content": "Response"}

            llm_call()

        assert session.turn_count == 1

    def test_mixed_decorator_and_manual(self):
        """Test mixing decorators with manual context."""
        with session_context(name="mixed-session") as session:

            @trace_llm()
            def decorated_llm():
                return {"role": "assistant", "content": "Decorated"}

            decorated_llm()

        assert session.turn_count >= 1


class TestDecoratorPerformance:
    """Test decorator performance and timing."""

    def test_duration_tracking(self):
        """Test that decorators track duration."""

        @trace_session(name="timing-session")
        def timed_function():
            @trace_llm()
            def slow_llm():
                time.sleep(0.1)  # Sleep 100ms
                return {"role": "assistant", "content": "Done"}

            return slow_llm()

        timed_function()
        session = get_current_session()

        turn = session.turns[0]
        # Duration should be at least 100ms
        assert turn.duration_ms >= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
