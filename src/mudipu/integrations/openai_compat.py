"""
OpenAI-compatible integration for automatic instrumentation.

This module provides wrappers and utilities for instrumenting OpenAI SDK calls.
"""
from typing import Optional, Any, Callable
import functools

from mudipu.decorators import trace_llm
from mudipu.context import trace_context


def traced_openai_chat(
    openai_client: Any,
    messages: list[dict],
    model: str = "gpt-4",
    **kwargs: Any
) -> Any:
    """
    Traced wrapper for OpenAI chat completions.
    
    Args:
        openai_client: OpenAI client instance
        messages: List of messages
        model: Model to use
        **kwargs: Additional arguments for the API call
        
    Returns:
        Chat completion response
        
    Example:
        >>> from openai import OpenAI
        >>> from mudipu.integrations.openai_compat import traced_openai_chat
        >>> 
        >>> client = OpenAI()
        >>> response = traced_openai_chat(
        ...     client,
        ...     messages=[{"role": "user", "content": "Hello!"}],
        ...     model="gpt-4"
        ... )
    """
    @trace_llm(model=model)
    def _call() -> Any:
        return openai_client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
    
    return _call()


class TracedOpenAI:
    """
    Wrapper for OpenAI client with automatic tracing.
    
    Example:
        >>> from openai import OpenAI
        >>> from mudipu import MudipuTracer
        >>> from mudipu.integrations.openai_compat import TracedOpenAI
        >>> 
        >>> tracer = MudipuTracer(session_name="my-app")
        >>> with tracer.trace_session():
        ...     client = TracedOpenAI(OpenAI())
        ...     response = client.chat.completions.create(
        ...         model="gpt-4",
        ...         messages=[{"role": "user", "content": "Hello!"}]
        ...     )
    """
    
    def __init__(self, openai_client: Any):
        """
        Initialize traced OpenAI client wrapper.
        
        Args:
            openai_client: Original OpenAI client
        """
        self._client = openai_client
        self.chat = TracedChatCompletions(openai_client.chat)


class TracedChatCompletions:
    """Wrapper for chat completions with tracing."""
    
    def __init__(self, chat_api: Any):
        """
        Initialize wrapper.
        
        Args:
            chat_api: Original chat API object
        """
        self._chat = chat_api
        self.completions = TracedCompletions(chat_api.completions)


class TracedCompletions:
    """Wrapper for completions endpoint with tracing."""
    
    def __init__(self, completions_api: Any):
        """
        Initialize wrapper.
        
        Args:
            completions_api: Original completions API object
        """
        self._completions = completions_api
    
    def create(self, model: str, messages: list[dict], **kwargs: Any) -> Any:
        """
        Create a chat completion with tracing.
        
        Args:
            model: Model to use
            messages: List of messages
            **kwargs: Additional arguments
            
        Returns:
            Chat completion response
        """
        @trace_llm(model=model)
        def _call() -> Any:
            return self._completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
        
        return _call()


def patch_openai(openai_module: Any) -> None:
    """
    Monkey-patch the OpenAI module for automatic tracing.
    
    Warning: This modifies the OpenAI module globally. Use with caution.
    
    Args:
        openai_module: The imported openai module
        
    Example:
        >>> import openai
        >>> from mudipu.integrations.openai_compat import patch_openai
        >>> 
        >>> patch_openai(openai)
        >>> # Now all OpenAI calls will be automatically traced
    """
    original_create = openai_module.chat.completions.create
    
    @functools.wraps(original_create)
    @trace_llm()
    def traced_create(*args: Any, **kwargs: Any) -> Any:
        return original_create(*args, **kwargs)
    
    openai_module.chat.completions.create = traced_create
