# CLI Reference

Complete reference for Mudipu command-line interface.

## Installation

```bash
pip install mudipu
```

Basic usage verification:

```bash
mudipu --version
mudipu --help
```

## Global Options

Available for all commands:

```bash
mudipu [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message |

## Commands

### `stats` - Session Statistics

Display comprehensive statistics for a trace file.

#### Usage

```bash
mudipu stats TRACE_FILE [OPTIONS]
```

#### Arguments

- `TRACE_FILE`: Path to trace JSON file (required)

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | TEXT | `table` | Output format: `table`, `json`, `csv` |
| `--verbose, -v` | FLAG | False | Show detailed statistics |

#### Examples

**Basic statistics:**

```bash
mudipu stats trace.json
```

**JSON output:**

```bash
mudipu stats trace.json --format json
```

**Verbose mode:**

```bash
mudipu stats trace.json --verbose
```

**Save to file:**

```bash
mudipu stats trace.json --format json > stats.json
```

#### Output

Default table output includes:

- Session ID and name
- Total turns
- Total tokens (prompt + completion)
- Total duration
- Average tokens per turn
- Average duration per turn
- Models used
- Tools called
- Metadata

### `analyze` - Session Analysis

Generate natural language summary of session.

#### Usage

```bash
mudipu analyze TRACE_FILE [OPTIONS]
```

#### Arguments

- `TRACE_FILE`: Path to trace JSON file (required)

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | FILE | stdout | Output file path |
| `--format, -f` | TEXT | `text` | Format: `text`, `markdown`, `json` |

#### Examples

**Basic analysis:**

```bash
mudipu analyze trace.json
```

**Markdown output:**

```bash
mudipu analyze trace.json --format markdown
```

**Save to file:**

```bash
mudipu analyze trace.json -o analysis.md --format markdown
```

#### Output

Includes:

- Executive summary
- Turn-by-turn breakdown
- Key patterns and insights
- Recommendations

### `health` - Context Health Analysis

Analyze conversation context health metrics.

**Requires:** `pip install mudipu[health]`

#### Usage

```bash
mudipu health TRACE_FILE [OPTIONS]
```

#### Arguments

- `TRACE_FILE`: Path to trace JSON file (required)

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--goal, -g` | TEXT | Auto-detected | Conversation goal/objective |
| `--threshold, -t` | FLOAT | `0.5` | Health score threshold (0.0-1.0) |
| `--visualize` | FLAG | False | Generate and display charts |
| `--output, -o` | FILE | None | Save visualization to file |
| `--format, -f` | TEXT | `text` | Output format: `text`, `json` |

#### Examples

**Basic health analysis:**

```bash
mudipu health trace.json
```

**With visualization:**

```bash
mudipu health trace.json --visualize
```

**Save visualization:**

```bash
mudipu health trace.json --visualize -o health.png
```

**Custom goal and threshold:**

```bash
mudipu health trace.json --goal "Debug API error" --threshold 0.6
```

**JSON output:**

```bash
mudipu health trace.json --format json
```

#### Output

Text format includes:

- Overall health score
- Per-turn metrics:
  - Relevance score
  - Duplicate ratio
  - Saturation score
  - Tool loop score
  - Novelty score
- Session-level metrics:
  - Growth rate
  - Drift score
  - Loop score
  - Progress score
  - Effectiveness score
- Health assessment (Healthy/Warning/Poor)
- Recommendations

Visualization shows:

- Time series of health scores
- Per-turn metric breakdown
- Session-level trends

### `export-html` - HTML Export

Export trace to interactive HTML report.

#### Usage

```bash
mudipu export-html TRACE_FILE [OPTIONS]
```

#### Arguments

- `TRACE_FILE`: Path to trace JSON file (required)

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o` | FILE | `trace.html` | Output HTML file path |
| `--theme` | TEXT | `light` | Theme: `light`, `dark`, `auto` |
| `--include-metadata` | FLAG | True | Include metadata in output |
| `--open-browser` | FLAG | False | Open in browser after export |

#### Examples

**Basic export:**

```bash
mudipu export-html trace.json
```

**Custom output file:**

```bash
mudipu export-html trace.json -o report.html
```

**Dark theme and auto-open:**

```bash
mudipu export-html trace.json --theme dark --open-browser
```

**Without metadata:**

```bash
mudipu export-html trace.json --no-include-metadata
```

#### Output

Interactive HTML with:

- Collapsible turn details
- Syntax-highlighted JSON
- Token usage charts
- Tool call timeline
- Duration metrics
- Search and filter capabilities

### `list-traces` - List Trace Files

List all trace files in a directory.

#### Usage

```bash
mudipu list-traces [DIRECTORY] [OPTIONS]
```

#### Arguments

- `DIRECTORY`: Directory to search (default: current directory)

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format, -f` | TEXT | `table` | Format: `table`, `json`, `csv` |
| `--sort` | TEXT | `modified` | Sort by: `name`, `modified`, `size`, `turns` |
| `--filter` | TEXT | None | Filter by name pattern (regex) |
| `--limit` | INT | None | Limit number of results |

#### Examples

**List traces in current directory:**

```bash
mudipu list-traces
```

**List traces in specific directory:**

```bash
mudipu list-traces ./traces
```

**JSON output:**

```bash
mudipu list-traces --format json
```

**Filter and sort:**

```bash
mudipu list-traces --filter ".*session.*" --sort size
```

**Limit results:**

```bash
mudipu list-traces --limit 10 --sort modified
```

#### Output

Table format includes:

- File name
- Session name
- Turns
- Tokens
- Duration
- Modified time
- File size

### `config` - Configuration Management

Manage Mudipu configuration.

#### Subcommands

##### `config show`

Display current configuration.

```bash
mudipu config show [OPTIONS]
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--format, -f` | TEXT | Format: `yaml`, `json`, `toml` |

**Examples:**

```bash
# YAML format (default)
mudipu config show

# JSON format
mudipu config show --format json
```

##### `config init`

Create configuration file with defaults.

```bash
mudipu config init [FILE] [OPTIONS]
```

**Arguments:**

- `FILE`: Config file path (default: `./mudipu.yaml`)

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--force, -f` | FLAG | Overwrite existing file |

**Examples:**

```bash
# Create in current directory
mudipu config init

# Custom location
mudipu config init ~/.mudipu/config.yaml

# Overwrite existing
mudipu config init --force
```

##### `config validate`

Validate configuration file.

```bash
mudipu config validate FILE
```

**Examples:**

```bash
mudipu config validate mudipu.yaml
```

**Output:**

```
✓ Configuration is valid
  Storage directory: ./traces
  Tracing enabled: true
  Format: json
```

### `version` - Version Information

Display detailed version information.

#### Usage

```bash
mudipu version [OPTIONS]
```

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--format, -f` | TEXT | Format: `text`, `json` |
| `--check-updates` | FLAG | Check for newer versions |

#### Examples

**Basic version:**

```bash
mudipu version
```

**JSON format:**

```bash
mudipu version --format json
```

**Check for updates:**

```bash
mudipu version --check-updates
```

#### Output

Includes:

- Mudipu version
- Python version
- Installation path
- Optional dependencies status
- Platform information

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Command line syntax error |
| 3 | File not found |
| 4 | Invalid input file |
| 5 | Configuration error |
| 6 | Missing optional dependency |

## Environment Variables

CLI respects all Mudipu environment variables. See [Configuration Guide](configuration.md).

Commonly used:

```bash
# Disable tracing
export MUDIPU_TRACING_ENABLED=false

# Custom storage
export MUDIPU_STORAGE_DIRECTORY="./my-traces"

# Adjust logging
export MUDIPU_LOGGING_LEVEL=DEBUG
```

## Output Formats

### Table Format

Default for most commands. Human-readable ASCII tables.

```
┌─────────────────┬───────┬────────┬──────────┐
│ Name            │ Turns │ Tokens │ Duration │
├─────────────────┼───────┼────────┼──────────┤
│ chat-session    │ 5     │ 1,234  │ 5,678 ms │
└─────────────────┴───────┴────────┴──────────┘
```

### JSON Format

Machine-readable, suitable for piping:

```json
{
  "session_id": "abc123",
  "name": "chat-session",
  "turns": 5,
  "total_tokens": 1234,
  "total_duration_ms": 5678
}
```

### CSV Format

Spreadsheet-compatible:

```csv
name,turns,tokens,duration_ms
chat-session,5,1234,5678
```

## Piping and Scripting

### Processing Multiple Files

```bash
# Analyze all traces
for file in traces/*.json; do
  mudipu stats "$file" >> all-stats.txt
done
```

### Shell Integration

```bash
# Get total tokens across all traces
mudipu list-traces --format json | jq '[.[] | .tokens] | add'
```

### JSON Output Processing

```bash
# Extract health scores
mudipu health trace.json --format json | jq '.overall_health_score'
```

### Conditional Actions

```bash
# Alert if health score is low
score=$(mudipu health trace.json --format json | jq -r '.overall_health_score')
if (( $(echo "$score < 0.5" | bc -l) )); then
  echo "Warning: Low health score!"
fi
```

## Batch Operations

### Analyze All Traces

```bash
#!/bin/bash
# analyze-all.sh

for trace in traces/*.json; do
  echo "Analyzing $trace..."
  mudipu analyze "$trace" -o "reports/$(basename $trace .json).md"
  mudipu health "$trace" --visualize -o "charts/$(basename $trace .json).png"
done
```

### Export All to HTML

```bash
#!/bin/bash
# export-all.sh

mkdir -p html-reports
mudipu list-traces --format json | jq -r '.[].path' | while read file; do
  output="html-reports/$(basename $file .json).html"
  mudipu export-html "$file" -o "$output"
done
```

## Debugging

### Verbose Mode

```bash
# Enable debug logging
export MUDIPU_LOGGING_LEVEL=DEBUG
mudipu stats trace.json --verbose
```

### Dry Run

Not directly supported, but can simulate:

```bash
# Check file without processing
mudipu stats trace.json --format json > /dev/null && echo "File is valid"
```

### Performance Profiling

```bash
# Time command execution
time mudipu health trace.json --visualize
```

## Common Workflows

### Daily Health Check

```bash
#!/bin/bash
# daily-check.sh

TODAY=$(date +%Y-%m-%d)
TRACES="traces/$TODAY-*.json"

for trace in $TRACES; do
  score=$(mudipu health "$trace" --format json | jq -r '.overall_health_score')
  if (( $(echo "$score < 0.5" | bc -l) )); then
    echo "⚠️  Low health: $trace ($score)"
  else
    echo "✓ Healthy: $trace ($score)"
  fi
done
```

### Automated Reporting

```bash
#!/bin/bash
# weekly-report.sh

WEEK=$(date +%Y-W%V)
OUTPUT="reports/$WEEK.md"

echo "# Weekly Report - $WEEK" > "$OUTPUT"
echo "" >> "$OUTPUT"

mudipu list-traces --format json | jq -r '.[].path' | while read trace; do
  echo "## $(basename $trace .json)" >> "$OUTPUT"
  mudipu analyze "$trace" --format markdown >> "$OUTPUT"
  echo "" >> "$OUTPUT"
done
```

## Troubleshooting

### Command Not Found

```bash
# Check installation
pip list | grep mudipu

# Reinstall
pip install --force-reinstall mudipu

# Check PATH (Windows)
echo %PATH%

# Check PATH (Linux/Mac)
echo $PATH
```

### Permission Denied

```bash
# Check permissions
ls -l trace.json

# Fix permissions
chmod 644 trace.json
```

### Missing Dependencies

```bash
# Health command requires optional dependencies
pip install mudipu[health]

# Install all optional dependencies
pip install mudipu[all]
```

### Invalid JSON

```bash
# Validate JSON
python -m json.tool trace.json

# Pretty print and save
python -m json.tool trace.json > trace-pretty.json
```

## See Also

- [Configuration Guide](configuration.md)
- [API Reference](api-reference.md)
- [Health Metrics](health-metrics.md)
- [Getting Started](getting-started.md)
