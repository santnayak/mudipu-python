# Examples

This directory contains example code demonstrating various features of the Mudipu SDK.

## Running Examples

Make sure you have installed the SDK and have your OpenAI API key set:

```bash
export OPENAI_API_KEY=your-api-key-here
```

Then run any example:

```bash
python examples/basic_example.py
```

## Available Examples

### 1. Basic Example (`basic_example.py`)
- Simple session tracing
- Using the `@trace_llm` decorator
- Automatic export of traces

### 2. Tools Example (`tools_example.py`)
- Tracing tool/function calls
- Using the `@trace_tool` decorator
- Combining LLM and tool tracing

### 3. Analysis Example (`analysis_example.py`)
- Loading and analyzing trace files
- Extracting statistics
- Cost estimation
- Finding performance issues

### 4. Config Example (`config_example.py`)
- Custom configuration
- Saving/loading config from YAML
- Using different export formats

### 5. Configuration File (`mudipu.example.yaml`)
- Comprehensive example configuration file
- Shows all available configuration options
- Includes comments explaining each setting
- Environment-specific configurations (production, development, testing)

**To use:**
```bash
# Copy to your project root
cp examples/mudipu.example.yaml mudipu.yaml

# Edit and customize
nano mudipu.yaml
```

## Output

All examples will create trace files in `.mudipu/traces/` (or the configured directory).

You can analyze these traces using:
- The Python API (see `analysis_example.py`)
- The CLI: `mudipu analyze .mudipu/traces/session_*.json`
- Opening the HTML files in a browser
