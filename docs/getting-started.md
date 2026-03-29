# Getting Started with Mudipu

This guide will help you get up and running with Mudipu in minutes.

## Installation

### Basic Installation

```bash
pip install mudipu
```

### Optional Dependencies

Install specific feature sets:

```bash
# For context health metrics
pip install mudipu[health]

# For OpenAI integration helpers
pip install mudipu[openai]

# Everything
pip install mudipu[all]
```

## Your First Trace

### Step 1: Import Mudipu

```python
from mudipu import trace_session, trace_llm
from openai import OpenAI

client = OpenAI()
```

### Step 2: Add Decorators

```python
@trace_session(name="my-first-agent")
def my_agent(question: str):
    @trace_llm(model="gpt-4")
    def ask_question(prompt):
        return client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    
    response = ask_question(question)
    return response.choices[0].message.content
```

### Step 3: Run It

```python
result = my_agent("What is machine learning?")
print(result)
```

That's it! A trace file is automatically saved to `.mudipu/traces/`.

## Viewing Your Traces

### CLI Analysis

```bash
# List all traces
mudipu list-traces .mudipu/traces/

# View statistics
mudipu stats .mudipu/traces/session_xyz.json

# Check health metrics
mudipu health .mudipu/traces/session_xyz.json
```

### Programmatic Analysis

```python
from mudipu.exporters import JSONExporter
from mudipu.analyzer import TraceAnalyzer

# Load trace
exporter = JSONExporter()
session = exporter.load(".mudipu/traces/session_xyz.json")

# Analyze
analyzer = TraceAnalyzer(session)
stats = analyzer.get_statistics()

print(f"Tokens: {stats['total_tokens']}")
print(f"Cost: ${analyzer.get_cost_estimate()['total']:.4f}")
```

## Context Managers vs Decorators

### Using Context Managers

```python
from mudipu import MudipuTracer

tracer = MudipuTracer(session_name="manual-session")

with tracer.trace_session():
    # Your code here
    response = client.chat.completions.create(...)
```

### Using Decorators (Recommended)

```python
@trace_session(name="decorator-session")
def my_function():
    # Automatically traced
    pass
```

## Configuration

### Default Configuration

By default, Mudipu:
- Saves traces to `.mudipu/traces/`
- Exports as JSON
- Does NOT send data anywhere

### Custom Configuration

#### Option 1: Code

```python
from mudipu import MudipuConfig, set_config
from pathlib import Path

config = MudipuConfig(
    enabled=True,
    trace_dir=Path("./my-traces"),
    auto_export=True,
    export_format="both",  # JSON and HTML
    debug=False
)

set_config(config)
```

#### Option 2: YAML File

Create `mudipu.yaml`:

```yaml
enabled: true
trace_dir: ./my-traces
auto_export: true
export_format: both
debug: false
```

Load it:

```python
from mudipu import MudipuConfig

config = MudipuConfig.from_yaml("mudipu.yaml")
set_config(config)
```

#### Option 3: Environment Variables

```bash
export MUDIPU_ENABLED=true
export MUDIPU_TRACE_DIR=./my-traces
export MUDIPU_AUTO_EXPORT=true
export MUDIPU_EXPORT_FORMAT=both
```

## Tracing Tools

Add `@trace_tool` to track function calls:

```python
from mudipu import trace_tool

@trace_tool("database_query")
def fetch_user_data(user_id: int):
    # Your database logic
    return {"name": "John", "email": "john@example.com"}
```

Tool calls appear in your traces with timing and results.

## Next Steps

- **[Health Metrics](./health-metrics.md)** - Learn about context quality analysis
- **[Configuration Guide](./configuration.md)** - Advanced configuration options
- **[API Reference](./api-reference.md)** - Complete API documentation
- **[Examples](../examples/)** - Real-world examples

## Common Patterns

### Multi-Turn Conversations

```python
@trace_session(name="chat-session")
def chat_conversation():
    messages = []
    
    for user_input in ["Hello", "What's the weather?", "Thanks!"]:
        messages.append({"role": "user", "content": user_input})
        
        @trace_llm(model="gpt-4")
        def get_response():
            return client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
        
        response = get_response()
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
```

### Agentic Workflows

```python
@trace_session(name="research-agent")
def research_agent(topic: str):
    # Plan
    plan = create_plan(topic)
    
    # Execute each step
    for step in plan:
        result = execute_step(step)
        
        # Tools are automatically traced
        if needs_web_search(result):
            search_results = web_search(step.query)
        
        if needs_analysis(result):
            analysis = analyze_data(search_results)
    
    # Synthesize
    return synthesize_results(results)
```

## Troubleshooting

### Traces not saving?

Check:
1. `config.enabled = True`
2. `config.auto_export = True`
3. Write permissions on `trace_dir`

### High overhead?

Try:
1. Disable debug mode: `config.debug = False`
2. Reduce export frequency
3. Use sampling for production

### Need help?

- [FAQ](./faq.md)
- [GitHub Issues](https://github.com/yourusername/mudipu-python/issues)
