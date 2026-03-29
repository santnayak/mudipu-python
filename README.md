# Mudipu Python SDK

> **Instrument, analyze, and optimize your AI agents**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/mudipu/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Mudipu is a lightweight Python SDK for tracing, analyzing, and improving LLM-powered applications. Add instrumentation in minutes, detect inefficiencies, and measure context health—all without sending data to external services.

## ✨ Key Features

- **🎯 Zero-friction instrumentation** - Add tracing with simple decorators
- **📊 Context health metrics** - Detect loops, drift, redundancy, and saturation
- **💰 Cost tracking** - Automatic token usage and cost estimation
- **🔍 Rich analysis** - CLI tools and programmatic APIs
- **🔒 Privacy-first** - Local-first architecture, no data leaves your machine
- **📤 Multiple export formats** - JSON, HTML, and more

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install mudipu

# With health metrics support
pip install mudipu[health]

# With all features
pip install mudipu[all]
```

### 30-Second Example

```python
from mudipu import trace_session, trace_llm
from openai import OpenAI

client = OpenAI()

@trace_session(name="my-agent")
def run_agent(question: str):
    @trace_llm(model="gpt-4")
    def ask_llm(prompt):
        return client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    
    response = ask_llm(question)
    return response.choices[0].message.content

# Run and automatically trace
result = run_agent("What is the capital of France?")

# Traces saved to .mudipu/traces/
```

### Analyze with CLI

```bash
# View health metrics
mudipu health .mudipu/traces/session_xyz.json

# See statistics
mudipu stats .mudipu/traces/session_xyz.json

# Generate visualization
mudipu health .mudipu/traces/session_xyz.json --visualize
```

## 📊 Context Health Metrics

Mudipu's unique health metrics help detect agent inefficiencies:

| Metric | What it detects | Score Range |
|--------|----------------|-------------|
| **Relevance** | Off-topic context | 0.0 - 1.0 |
| **Duplicate Ratio** | Repeated information | 0.0 - 1.0 |
| **Tool Loops** | Repeated tool calls | 0.0 - 1.0 |
| **Drift** | Goal misalignment | 0.0 - 1.0 |
| **Novelty** | Progress tracking | 0.0 - 1.0 |
| **Overall Health** | Combined score | 0.0 - 1.0 |

**Example output:**

```
╭───────────────────────────────────────────────────╮
│ Session Health: 0.687 🟡 MODERATE                 │
│                                                   │
│ ├─ Context Growth: +58.1 tokens/turn              │
│ ├─ Drift Score: 0.024 ✓                           |
│ ├─ Loop Score: 0.333 ⚠️                           │
│ ├─ Progress: 0.333                                │
│ └─ Effectiveness: 0.700                           │
│                                                   │
│ ⚠️  Tool loops detected                           │
╰───────────────────────────────────────────────────╯
```

👉 [**Learn more about health metrics**](./docs/health-metrics.md)

## 📖 Documentation

- **[Getting Started Guide](./docs/getting-started.md)** - Installation and basic usage
- **[Health Metrics Deep Dive](./docs/health-metrics.md)** - Understanding context health
- **[API Reference](./docs/api-reference.md)** - Complete API documentation
- **[Configuration Guide](./docs/configuration.md)** - Customize SDK behavior
- **[CLI Reference](./docs/cli-reference.md)** - Command-line tools
- **[Examples](./examples/)** - Real-world use cases

## 🎯 Use Cases

- **Debug agent loops** - Detect when your agent gets stuck
- **Optimize context** - Identify redundant information
- **Track costs** - Monitor token usage and expenses
- **Improve quality** - Measure goal alignment over time
- **Analyze traces** - Understand agent behavior patterns

## 🛠️ Architecture

Mudipu is designed to be:

1. **Local-first**: All data stays on your machine
2. **Lightweight**: Minimal performance overhead
3. **Framework-agnostic**: Works with any LLM library
4. **Extensible**: Add custom metrics and exporters

```
Your Agent Code
    ↓
[Mudipu Decorators]
    ↓
[Trace Capture]
    ↓
┌──────┴──────┬──────────┐
↓             ↓          ↓
Local JSON   HTML    Analysis CLI
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - see [LICENSE](./LICENSE) for details.

## 🔗 Links

- **Documentation**: [./docs/](./docs/)
- **PyPI**: https://pypi.org/project/mudipu/
- **GitHub**: https://github.com/yourusername/mudipu-python
- **Issues**: https://github.com/yourusername/mudipu-python/issues

## ⭐ Acknowledgments

Built with:
- [sentence-transformers](https://github.com/UKPLab/sentence-transformers) for semantic analysis
- [Rich](https://github.com/Textualize/rich) for beautiful CLI output
- [Click](https://click.palletsprojects.com/) for command-line interface

---

