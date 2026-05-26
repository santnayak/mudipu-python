"""
Decorators for automatic instrumentation of LLM calls, tools, and sessions.
"""

import time
import functools
from typing import Callable, Optional, Any

from mudipu.context import trace_context
from mudipu.config import get_config


def trace_llm(
    model: Optional[str] = None,
    extract_messages: Optional[Callable] = None,
    extract_response: Optional[Callable] = None,
) -> Callable:
    """
    Decorator for tracing LLM calls.

    Args:
        model: Model name (if None, will try to extract from kwargs)
        extract_messages: Function to extract messages from args/kwargs
        extract_response: Function to extract response from return value

    Example:
        @trace_llm(model="gpt-4")
        def call_openai(messages):
            return client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            config = get_config()

            # Skip if tracing disabled or no active session
            if not config.enabled or not trace_context.is_active():
                return func(*args, **kwargs)

            # Extract messages
            if extract_messages:
                messages = extract_messages(*args, **kwargs)
            elif "messages" in kwargs:
                messages = kwargs["messages"]
            elif len(args) > 0 and isinstance(args[0], list):
                messages = args[0]
            else:
                messages = []

            # Extract model
            actual_model = model or kwargs.get("model", "unknown")

            # Extract tools if present
            tools = kwargs.get("tools", [])

            # Time the call
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Extract response
                if extract_response:
                    response_data = extract_response(result)
                else:
                    response_data = _default_extract_response(result)

                # Import here to avoid circular dependency
                from mudipu.capture.llm import capture_llm_turn

                # Capture the turn
                capture_llm_turn(
                    request_messages=messages,
                    response_data=response_data,
                    model=actual_model,
                    tools=tools,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                # Log error turn
                from mudipu.capture.llm import capture_llm_turn

                capture_llm_turn(
                    request_messages=messages,
                    response_data={"error": str(e)},
                    model=actual_model,
                    tools=tools,
                    duration_ms=duration_ms,
                )

                raise

        return wrapper

    return decorator


def trace_tool(tool_name: Optional[str] = None, name: Optional[str] = None) -> Callable:
    """
    Decorator for tracing tool/function calls.

    Args:
        tool_name: Name of the tool (defaults to function name)
        name: Alias for tool_name for convenience

    Example:
        @trace_tool("web_search")
        def search_web(query: str):
            return perform_search(query)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            config = get_config()

            # Skip if tracing disabled or no active session
            if not config.enabled or not trace_context.is_active():
                return func(*args, **kwargs)

            actual_tool_name = tool_name or name or func.__name__

            # Time the call
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Capture tool execution
                from mudipu.capture.tools import capture_tool_execution

                capture_tool_execution(
                    tool_name=actual_tool_name,
                    arguments={"args": args, "kwargs": kwargs},
                    result=result,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                # Capture tool error
                from mudipu.capture.tools import capture_tool_execution

                capture_tool_execution(
                    tool_name=actual_tool_name,
                    arguments={"args": args, "kwargs": kwargs},
                    result=None,
                    error=str(e),
                    duration_ms=duration_ms,
                )

                raise

        return wrapper

    return decorator


def trace_session(
    name: Optional[str] = None, tags: Optional[list[str]] = None, metadata: Optional[dict[str, Any]] = None
) -> Callable:
    """
    Decorator for automatic session management.

    Args:
        name: Session name
        tags: Session tags
        metadata: Additional metadata for the session

    Example:
        @trace_session(name="chatbot", tags=["production"])
        def run_chatbot():
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            config = get_config()

            # Skip if tracing disabled
            if not config.enabled:
                return func(*args, **kwargs)

            from mudipu.tracer import MudipuTracer

            tracer = MudipuTracer(session_name=name, tags=tags)

            with tracer.trace_session():
                # Add metadata if provided
                if metadata and tracer.session:
                    tracer.session.metadata.update(metadata)
                return func(*args, **kwargs)

        return wrapper

    return decorator


def _default_extract_response(result: Any) -> dict:
    """
    Default response extraction for common LLM SDK response formats.

    Args:
        result: Response object from LLM call

    Returns:
        Dictionary with extracted response data
    """
    response_data: dict[str, Any] = {}

    # Handle OpenAI-style responses
    if hasattr(result, "choices") and len(result.choices) > 0:
        choice = result.choices[0]

        if hasattr(choice, "message"):
            message = choice.message
            response_data["role"] = getattr(message, "role", "assistant")
            response_data["content"] = getattr(message, "content", "")

            # Extract tool calls if present
            if hasattr(message, "tool_calls") and message.tool_calls:
                response_data["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]

        # Extract usage
        if hasattr(result, "usage"):
            usage = result.usage
            response_data["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }

    # Fallback: try to convert to dict
    elif hasattr(result, "model_dump"):
        response_data = result.model_dump()
    elif hasattr(result, "dict"):
        response_data = result.dict()
    elif isinstance(result, dict):
        response_data = result
    else:
        response_data = {"raw": str(result)}

    return response_data
