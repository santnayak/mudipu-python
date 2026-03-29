# API Reference

Complete API documentation for Mudipu Python SDK.

## Core Tracing API

### Session Context Manager

```python
from mudipu.context import session_context

with session_context(
    name: str = "session",
    metadata: dict = None,
    trace_id: str = None
) -> Session:
    """
    Create a traced session context.
    
    Args:
        name: Session name for identification
        metadata: Optional metadata dict
        trace_id: Optional trace ID (auto-generated if not provided)
    
    Returns:
        Session object with captured turns
    
    Example:
        with session_context(name="chat", metadata={"user": "alice"}) as session:
            # Your code here
            pass
        
        print(f"Captured {session.turn_count} turns")
    """
```

### Decorators

#### @trace_session

```python
from mudipu.decorators import trace_session

@trace_session(
    name: str = "session",
    metadata: dict = None,
    trace_id: str = None
)
def my_function():
    """
    Decorator to trace an entire session.
    
    Args:
        name: Session name
        metadata: Optional metadata
        trace_id: Optional trace ID
    
    Example:
        @trace_session(name="analysis", metadata={"version": "1.0"})
        def analyze_data():
            # All LLM and tool calls will be traced
            result = llm_call()
            return result
    """
```

#### @trace_llm

```python
from mudipu.decorators import trace_llm

@trace_llm(
    request_messages: list = None,
    usage_info: dict = None,
    model: str = None
)
def my_llm_call():
    """
    Decorator to trace an LLM turn.
    
    Args:
        request_messages: Optional list of input messages
        usage_info: Optional usage information dict
        model: Optional model identifier
    
    Returns:
        Response message dict with 'role' and 'content'
    
    Example:
        @trace_llm(model="gpt-4")
        def ask_question(prompt):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                "role": "assistant",
                "content": response.choices[0].message.content
            }
    """
```

#### @trace_tool

```python
from mudipu.decorators import trace_tool

@trace_tool(name: str)
def my_tool():
    """
    Decorator to trace a tool call.
    
    Args:
        name: Tool name identifier
    
    Example:
        @trace_tool(name="web_search")
        def search_web(query: str) -> dict:
            results = perform_search(query)
            return {"results": results}
    """
```

## Models

### Session

```python
from mudipu.models import Session

class Session:
    """
    Complete conversation session.
    
    Attributes:
        session_id: Unique session identifier
        trace_id: Associated trace identifier
        name: Session name
        turns: List of conversation turns
        metadata: Optional metadata dict
        created_at: Session creation timestamp
        updated_at: Last update timestamp
    
    Computed Properties:
        turn_count: Number of turns (int)
        total_tokens: Total tokens across all turns (int)
        total_duration_ms: Total duration in milliseconds (int)
    """
    
    @classmethod
    def from_file(cls, path: str) -> 'Session':
        """Load session from JSON file."""
    
    def to_file(self, path: str) -> None:
        """Save session to JSON file."""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
    
    def to_json(self) -> str:
        """Convert to JSON string."""
```

### Turn

```python
from mudipu.models import BaseTurn, CompleteTurn

class BaseTurn:
    """
    Single conversation turn.
    
    Attributes:
        turn_number: Turn sequence number (1-indexed)
        request_messages: List of input messages
        response_message: Output message
        tool_calls_detected: List of tool calls
        usage: Token usage information
        duration_ms: Turn duration in milliseconds
        model: Model identifier
        metadata: Optional metadata dict
    """

class CompleteTurn(BaseTurn):
    """
    Turn with additional computed fields.
    
    Additional Attributes:
        embeddings: Semantic embeddings (list of floats)
        health_metrics: Per-turn health scores (dict)
    """
```

### Message

```python
from mudipu.models import Message

class Message:
    """
    Chat message.
    
    Attributes:
        role: Message role ("user", "assistant", "system", "tool")
        content: Message content text
        name: Optional sender name
    """
```

### Usage

```python
from mudipu.models import Usage

class Usage:
    """
    Token usage information.
    
    Attributes:
        prompt_tokens: Input tokens
        completion_tokens: Output tokens
        total_tokens: Total tokens
        estimated_cost: Optional cost estimate (float)
    """
```

### ToolCall

```python
from mudipu.models import ToolCall

class ToolCall:
    """
    Tool/function call record.
    
    Attributes:
        id: Optional call identifier
        name: Tool name
        arguments: Arguments dict
        result: Optional result value
    """
```

## Analysis API

### TraceAnalyzer

```python
from mudipu.analyzer import TraceAnalyzer

analyzer = TraceAnalyzer(session: Session)

# Get basic statistics
stats = analyzer.get_statistics()
# Returns: {
#     "total_turns": int,
#     "total_tokens": int,
#     "total_duration_ms": int,
#     "avg_tokens_per_turn": float,
#     "avg_duration_per_turn": float,
#     "models_used": list,
#     "tools_used": list
# }

# Get health metrics (requires mudipu[health])
health = analyzer.get_health_metrics(
    goal: str = None,
    threshold: float = 0.5,
    progress_callback: callable = None
)
# Returns: dict with per-turn and session-level metrics

# Generate summary
summary = analyzer.get_summary()
# Returns: str with formatted analysis
```

### ContextHealthAnalyzer

```python
from mudipu.analyzer.health import ContextHealthAnalyzer

analyzer = ContextHealthAnalyzer(
    session: Session,
    goal: str = None,
    history_limit: int = 5,
    progress_callback: callable = None
)

# Analyze single turn
turn_health = analyzer.analyze_turn(turn: BaseTurn, history: list)
# Returns: {
#     "relevance_score": float,
#     "duplicate_ratio": float,
#     "saturation_score": float,
#     "tool_loop_score": float,
#     "novelty_score": float,
#     "combined_health_score": float
# }

# Get session metrics
session_metrics = analyzer.get_session_metrics(turns_health: list)
# Returns: {
#     "growth_rate": float,
#     "drift_score": float,
#     "loop_score": float,
#     "progress_score": float,
#     "effectiveness_score": float,
#     "overall_health_score": float
# }

# Full analysis
full_analysis = analyzer.get_full_analysis()
# Returns complete health report with visualization
```

## Configuration API

### MudipuConfig

```python
from mudipu.config import MudipuConfig, get_config, set_config

# Create config
config = MudipuConfig()

# Load from YAML
config = MudipuConfig.from_yaml("path/to/config.yaml")

# Access settings
config.storage.directory  # str
config.storage.format  # "json" | "pickle" | "msgpack"
config.tracing.enabled  # bool
config.tracing.auto_flush  # bool

# Global config singleton
config = get_config()
set_config(custom_config)
```

## Export API

### HTML Export

```python
from mudipu.exporters import export_to_html

html = export_to_html(
    session: Session,
    output_path: str = None,
    include_metadata: bool = True
)
# Returns HTML string, optionally saves to file
```

### JSON Export

```python
# Sessions have built-in JSON export
session.to_file("output.json")

# Or use model methods
json_str = session.to_json()
dict_data = session.to_dict()
```

## Utility Functions

### Tracer Utilities

```python
from mudipu.tracer import (
    get_current_session,
    set_current_session,
    clear_context,
    get_tracer
)

# Get active session
session = get_current_session()

# Set custom session
set_current_session(my_session)

# Clear context
clear_context()

# Get global tracer
tracer = get_tracer()
```

### File Operations

```python
from mudipu.utils import (
    load_trace,
    save_trace,
    list_traces
)

# Load trace from file
session = load_trace("trace.json")

# Save trace
save_trace(session, "output.json")

# List all traces in directory
traces = list_traces("./traces")
```

## Exception Handling

### Common Exceptions

```python
from mudipu.exceptions import (
    MudipuError,
    ConfigurationError,
    TraceNotFoundError,
    InvalidSessionError
)

try:
    session = load_trace("missing.json")
except TraceNotFoundError as e:
    print(f"Trace not found: {e}")

try:
    config = MudipuConfig.from_yaml("invalid.yaml")
except ConfigurationError as e:
    print(f"Config error: {e}")
```

## Type Hints

Mudipu is fully typed with mypy support:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mudipu.models import Session, BaseTurn
    from mudipu.analyzer import TraceAnalyzer

def process_session(session: Session) -> dict:
    analyzer: TraceAnalyzer = TraceAnalyzer(session)
    return analyzer.get_statistics()
```

## See Also

- [Getting Started Guide](getting-started.md)
- [Health Metrics Documentation](health-metrics.md)
- [Configuration Guide](configuration.md)
- [CLI Reference](cli-reference.md)
