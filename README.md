# Mudipu Python SDK

> Developer-facing instrumentation package for AI agents and LLM applications

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

> **⚠️ WORK IN PROGRESS**  
> This SDK is under active development and may contain bugs or incomplete features. We welcome your feedback and contributions! If you encounter any issues or have suggestions, please [open an issue](https://github.com/santnayak/mudipu-python/issues) on GitHub.

---

Mudipu SDK provides ergonomic, decorator-based instrumentation for tracking LLM interactions with minimal code changes. Capture, analyze, and export detailed traces of your AI applications locally or to the Mudipu platform (see repository mudipu).

## Features

- **Zero-friction instrumentation** - Add tracing with simple decorators
- **Rich analysis** - Detailed statistics, cost estimates, and performance metrics
- **Multiple export formats** - JSON, HTML.
- **Privacy-first** - Local-first with optional platform sync and built-in redaction
- **CLI tools** - Analyze traces from the command line
- **Easy integrations** - OpenAI and other LLM SDK wrappers
- **Session management** - Automatic context tracking across turns

## 🚀 Quick Start

### Installation

```bash
pip install mudipu
```

For OpenAI integration:
```bash
pip install mudipu[openai]
```

For platform integration (sending traces to Mudipu platform) - **WORK IN PROGRESS**:
```bash
pip install mudipu[platform] 
```

Install everything:
```bash
pip install mudipu[all]
```

### Basic Usage

```python
from mudipu import MudipuTracer, trace_llm
from openai import OpenAI

# Initialize tracer
tracer = MudipuTracer(session_name="my-chatbot")

# Trace a session
with tracer.trace_session():
    client = OpenAI()
    
    @trace_llm(model="gpt-4")
    def ask_llm(question):
        return client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}]
        )
    
    response = ask_llm("What is the capital of France?")
    print(response.choices[0].message.content)

# Traces are automatically exported to .mudipu/traces/
```

### Using Decorators

```python
from mudipu import trace_session, trace_llm, trace_tool

@trace_session(name="customer-support", tags=["production"])
def handle_customer_query(query: str) -> str:
    """Handle a customer support query."""
    
    # LLM calls are automatically traced
    response = call_llm(query)
    
    # Tool calls are automatically traced
    if needs_database_lookup(response):
        data = fetch_customer_data(query)
    
    return generate_response(response, data)

@trace_llm(model="gpt-4-turbo")
def call_llm(query: str):
    # Your LLM call here
    pass

@trace_tool("database_lookup")
def fetch_customer_data(query: str):
    # Your tool logic here
    pass
```

## 📖 Core Concepts

### Tracer

The `MudipuTracer` is the central component for capturing LLM interactions:

```python
from mudipu import MudipuTracer

tracer = MudipuTracer(
    session_name="my-app",
    tags=["production", "v2"]
)

# Manual session management
tracer.start_session()
# ... your code ...
session = tracer.end_session()

# Or use context manager
with tracer.trace_session():
    # Your traced code here
    pass
```

### Configuration

Configure behavior via code or YAML:

```python
from mudipu import MudipuConfig, set_config

config = MudipuConfig(
    enabled=True,
    trace_dir=Path(".mudipu/traces"),
    auto_export=True,
    export_format="both",  # "json", "html", or "both"
    redact_enabled=True,
    platform_enabled=False,
)

set_config(config)
```

Or use environment variables:
```bash
export MUDIPU_ENABLED=true
export MUDIPU_TRACE_DIR=./traces
export MUDIPU_PLATFORM_URL=https://platform.mudipu.dev
export MUDIPU_API_KEY=your-api-key
```

Or create a `mudipu.yaml`:
```yaml
enabled: true
trace_dir: .mudipu/traces
auto_export: true
export_format: both
redact_enabled: false
platform_enabled: false
debug: false
```

### Analysis

Analyze traces programmatically:

```python
from mudipu.analyzer import TraceAnalyzer, SummaryGenerator
from mudipu.exporters import JSONExporter

# Load a trace
exporter = JSONExporter()
session = exporter.load(Path(".mudipu/traces/session_xyz.json"))

# Analyze
analyzer = TraceAnalyzer(session)
stats = analyzer.get_statistics()

print(f"Total turns: {stats['turn_count']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Average duration: {stats['avg_duration_ms']}ms")

# Cost estimation
costs = analyzer.get_cost_estimate()
print(f"Estimated cost: ${costs['total']:.4f}")

# Generate summary
summary_gen = SummaryGenerator(session)
print(summary_gen.generate_text_summary())
```

## 🖥️ CLI Usage

The SDK includes a powerful CLI for analyzing traces:

```bash
# Check version
mudipu --version
mudipu -v

# Analyze a trace file
mudipu analyze .mudipu/traces/session_xyz.json

# Show detailed statistics
mudipu stats .mudipu/traces/session_xyz.json

# Export to HTML
mudipu export-html .mudipu/traces/session_xyz.json -o report.html

# List all traces
mudipu list-traces .mudipu/traces/

# Show configuration
mudipu config show

# Initialize config file
mudipu config init mudipu.yaml
```

## 🔌 Integrations

### OpenAI

```python
from mudipu.integrations.openai_compat import TracedOpenAI
from openai import OpenAI

# Wrap the client
client = TracedOpenAI(OpenAI())

# Use as normal - automatically traced
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Or use the helper function:

```python
from mudipu.integrations.openai_compat import traced_openai_chat
from openai import OpenAI

client = OpenAI()
response = traced_openai_chat(
    client,
    messages=[{"role": "user", "content": "Hello!"}],
    model="gpt-4"
)
```

## 📊 Exporters

### JSON Export

```python
from mudipu.exporters import JSONExporter

exporter = JSONExporter()
exporter.export(session)  # Exports to configured trace_dir
```

### HTML Export

```python
from mudipu.exporters import HTMLExporter

exporter = HTMLExporter()
path = exporter.export(session)
print(f"HTML report: {path}")
```

### Platform Export

**Note:** Platform export requires the `platform` extra. Install with: `pip install mudipu[platform]`

```python
from mudipu.exporters import PlatformExporter

exporter = PlatformExporter(
    platform_url="nats://platform.mudipu.dev:4222",
    api_key="your-api-key"
)
exporter.export(session)  # Sends to platform via NATS
```

## 🔒 Privacy & Redaction

Enable automatic redaction of sensitive data:

```python
from mudipu import MudipuConfig

config = MudipuConfig(
    redact_enabled=True,
    redact_patterns=[
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # emails
        r'\bsk-[a-zA-Z0-9]{32,}\b',  # API keys
        # Add custom patterns
    ]
)
```

Or use the redactor directly:

```python
from mudipu.utils.redact import redact

data = {
    "email": "user@example.com",
    "message": "My API key is sk-abc123xyz"
}

clean_data = redact(data)
# {"email": "[REDACTED]", "message": "My API key is [REDACTED]"}
```

## 📁 Project Structure

```
mudipu-sdk-python/
├── src/
│   └── mudipu/
│       ├── __init__.py          # Main exports
│       ├── version.py           # Version info
│       ├── config.py            # Configuration management
│       ├── settings.py          # Environment settings
│       ├── models.py            # Data models
│       ├── tracer.py            # Core tracer
│       ├── context.py           # Thread-local context
│       ├── decorators.py        # Instrumentation decorators
│       ├── capture/             # Capture modules
│       ├── exporters/           # Export formats
│       ├── analyzer/            # Analysis tools
│       ├── integrations/        # LLM SDK integrations
│       ├── cli/                 # CLI interface
│       └── utils/               # Utilities
├── tests/                       # Test suite
├── examples/                    # Usage examples
└── docs/                        # Documentation
```




## 📝 License

MIT License 


