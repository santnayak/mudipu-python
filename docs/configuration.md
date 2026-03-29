# Configuration Guide

Complete guide to configuring Mudipu for your needs.

## Configuration Methods

Mudipu supports three configuration methods, in order of precedence:

1. **Environment Variables** (highest priority)
2. **YAML Configuration Files**
3. **Code-based Configuration**
4. **Default Values** (lowest priority)

## Quick Start

### 1. Using Defaults

```python
from mudipu.decorators import trace_session

# Uses all default settings
@trace_session(name="my-session")
def my_function():
    pass
```

### 2. Environment Variables

```bash
export MUDIPU_STORAGE_DIRECTORY="./my-traces"
export MUDIPU_STORAGE_FORMAT="json"
export MUDIPU_TRACING_ENABLED="true"
```

```python
# Automatically picks up environment variables
from mudipu.decorators import trace_session
```

### 3. YAML Configuration

```yaml
# mudipu.yaml
storage:
  directory: "./traces"
  format: "json"
  auto_cleanup: false

tracing:
  enabled: true
  auto_flush: true
  include_source: true
```

```python
from mudipu.config import MudipuConfig

config = MudipuConfig.from_yaml("mudipu.yaml")
```

### 4. Programmatic Configuration

```python
from mudipu.config import MudipuConfig, set_config

config = MudipuConfig()
config.storage.directory = "./custom-traces"
config.storage.format = "msgpack"
config.tracing.enabled = True

set_config(config)
```

## Configuration Options

### Storage Configuration

#### `storage.directory`

**Type:** `str`  
**Default:** `"./mudipu-traces"`  
**Description:** Directory where trace files are stored

```yaml
storage:
  directory: "./traces"
```

```bash
export MUDIPU_STORAGE_DIRECTORY="./traces"
```

```python
config.storage.directory = "./traces"
```

#### `storage.format`

**Type:** `"json" | "pickle" | "msgpack"`  
**Default:** `"json"`  
**Description:** Serialization format for trace files

- `json`: Human-readable, widely compatible
- `pickle`: Python-specific, preserves all types
- `msgpack`: Compact binary format

```yaml
storage:
  format: "json"
```

```bash
export MUDIPU_STORAGE_FORMAT="json"
```

```python
config.storage.format = "json"
```

#### `storage.auto_cleanup`

**Type:** `bool`  
**Default:** `false`  
**Description:** Automatically delete old trace files

```yaml
storage:
  auto_cleanup: true
  cleanup_days: 30  # Delete traces older than 30 days
```

#### `storage.compression`

**Type:** `bool`  
**Default:** `false`  
**Description:** Enable gzip compression for trace files

```yaml
storage:
  compression: true
```

### Tracing Configuration

#### `tracing.enabled`

**Type:** `bool`  
**Default:** `true`  
**Description:** Master switch for tracing functionality

```yaml
tracing:
  enabled: true
```

```bash
export MUDIPU_TRACING_ENABLED="true"
```

```python
config.tracing.enabled = True
```

**Use case:** Disable tracing in production:

```python
import os
from mudipu.config import get_config

config = get_config()
config.tracing.enabled = os.getenv("ENVIRONMENT") != "production"
```

#### `tracing.auto_flush`

**Type:** `bool`  
**Default:** `true`  
**Description:** Automatically save sessions when complete

```yaml
tracing:
  auto_flush: true
```

```bash
export MUDIPU_TRACING_AUTO_FLUSH="true"
```

If `false`, you must manually save sessions:

```python
from mudipu.context import session_context

with session_context(name="manual") as session:
    # ... your code ...
    pass

# Manually save
session.to_file("./traces/manual-session.json")
```

#### `tracing.include_source`

**Type:** `bool`  
**Default:** `false`  
**Description:** Include source code snippets in traces

```yaml
tracing:
  include_source: true
```

⚠️ **Warning:** May expose sensitive code in traces

#### `tracing.sample_rate`

**Type:** `float` (0.0 - 1.0)  
**Default:** `1.0`  
**Description:** Fraction of sessions to trace

```yaml
tracing:
  sample_rate: 0.1  # Trace 10% of sessions
```

Useful for high-volume production:

```python
config.tracing.sample_rate = 0.01  # 1% sampling
```

### Health Analysis Configuration

#### `health.model_name`

**Type:** `str`  
**Default:** `"all-MiniLM-L6-v2"`  
**Description:** Sentence transformer model for embeddings

```yaml
health:
  model_name: "all-MiniLM-L6-v2"
```

**Options:**
- `all-MiniLM-L6-v2`: Fast, good quality (default)
- `all-mpnet-base-v2`: Higher quality, slower
- `paraphrase-multilingual-MiniLM-L12-v2`: Multilingual support

#### `health.similarity_threshold`

**Type:** `float` (0.0 - 1.0)  
**Default:** `0.7`  
**Description:** Threshold for detecting duplicate content

```yaml
health:
  similarity_threshold: 0.7
```

#### `health.history_limit`

**Type:** `int`  
**Default:** `5`  
**Description:** Number of previous turns to consider for context

```yaml
health:
  history_limit: 5
```

Larger values:
- ✅ Better loop detection
- ❌ Slower analysis

#### `health.cache_embeddings`

**Type:** `bool`  
**Default:** `true`  
**Description:** Cache embeddings for faster repeated analysis

```yaml
health:
  cache_embeddings: true
```

## Configuration Files

### File Locations

Mudipu searches for configuration in this order:

1. `./mudipu.yaml` (current directory)
2. `~/.mudipu/config.yaml` (user config)
3. `/etc/mudipu/config.yaml` (system config, Linux/Mac)

### Creating Configuration File

#### Using CLI

```bash
mudipu config init
# Creates ./mudipu.yaml with defaults

mudipu config init ~/.mudipu/config.yaml
# Creates config in custom location
```

#### Manual Creation

Create `mudipu.yaml`:

```yaml
# Mudipu Configuration

storage:
  directory: "./traces"
  format: "json"
  compression: false
  auto_cleanup: false

tracing:
  enabled: true
  auto_flush: true
  include_source: false
  sample_rate: 1.0

health:
  model_name: "all-MiniLM-L6-v2"
  similarity_threshold: 0.7
  history_limit: 5
  cache_embeddings: true

logging:
  level: "INFO"
  file: "./mudipu.log"
```

### Viewing Current Configuration

```bash
mudipu config show
```

```python
from mudipu.config import get_config

config = get_config()
print(config.model_dump_json(indent=2))
```

## Environment Variables

### Complete List

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MUDIPU_STORAGE_DIRECTORY` | str | `./mudipu-traces` | Trace storage directory |
| `MUDIPU_STORAGE_FORMAT` | str | `json` | Serialization format |
| `MUDIPU_STORAGE_COMPRESSION` | bool | `false` | Enable compression |
| `MUDIPU_STORAGE_AUTO_CLEANUP` | bool | `false` | Auto-delete old traces |
| `MUDIPU_TRACING_ENABLED` | bool | `true` | Enable/disable tracing |
| `MUDIPU_TRACING_AUTO_FLUSH` | bool | `true` | Auto-save sessions |
| `MUDIPU_TRACING_INCLUDE_SOURCE` | bool | `false` | Include source code |
| `MUDIPU_TRACING_SAMPLE_RATE` | float | `1.0` | Sampling rate (0.0-1.0) |
| `MUDIPU_HEALTH_MODEL_NAME` | str | `all-MiniLM-L6-v2` | Embedding model |
| `MUDIPU_HEALTH_SIMILARITY_THRESHOLD` | float | `0.7` | Duplicate threshold |
| `MUDIPU_HEALTH_HISTORY_LIMIT` | int | `5` | Context history size |
| `MUDIPU_LOGGING_LEVEL` | str | `INFO` | Logging level |

### Setting Environment Variables

#### Linux/Mac

```bash
# Temporary (current shell)
export MUDIPU_STORAGE_DIRECTORY="./traces"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export MUDIPU_STORAGE_DIRECTORY="./traces"' >> ~/.bashrc
```

#### Windows PowerShell

```powershell
# Temporary (current session)
$env:MUDIPU_STORAGE_DIRECTORY = "./traces"

# Permanent (user level)
[System.Environment]::SetEnvironmentVariable(
    "MUDIPU_STORAGE_DIRECTORY",
    "./traces",
    "User"
)
```

#### Windows CMD

```cmd
set MUDIPU_STORAGE_DIRECTORY=./traces
```

#### .env Files

Create `.env` in your project root:

```env
MUDIPU_STORAGE_DIRECTORY=./traces
MUDIPU_STORAGE_FORMAT=json
MUDIPU_TRACING_ENABLED=true
```

Use with `python-dotenv`:

```python
from dotenv import load_dotenv

load_dotenv()

# Mudipu will now use .env values
from mudipu.decorators import trace_session
```

## Common Configuration Scenarios

### Development Environment

```yaml
# dev-config.yaml
storage:
  directory: "./dev-traces"
  format: "json"  # Human-readable for debugging
  compression: false

tracing:
  enabled: true
  auto_flush: true
  include_source: true  # Helpful for debugging

health:
  cache_embeddings: false  # Always fresh analysis

logging:
  level: "DEBUG"
```

### Production Environment

```yaml
# prod-config.yaml
storage:
  directory: "/var/log/mudipu"
  format: "msgpack"  # Compact
  compression: true
  auto_cleanup: true
  cleanup_days: 7

tracing:
  enabled: true
  auto_flush: true
  include_source: false  # Security
  sample_rate: 0.1  # 10% sampling to reduce overhead

health:
  cache_embeddings: true

logging:
  level: "WARNING"
  file: "/var/log/mudipu/mudipu.log"
```

```python
import os
from mudipu.config import MudipuConfig, set_config

# Load environment-specific config
env = os.getenv("ENVIRONMENT", "dev")
config = MudipuConfig.from_yaml(f"{env}-config.yaml")
set_config(config)
```

### Testing Environment

```yaml
# test-config.yaml
storage:
  directory: "/tmp/mudipu-tests"
  format: "pickle"  # Preserve all Python types

tracing:
  enabled: true
  auto_flush: false  # Manual control in tests
  sample_rate: 1.0  # Trace everything

logging:
  level: "ERROR"  # Quiet during tests
```

### CI/CD Pipeline

```bash
# .github/workflows/test.yml
env:
  MUDIPU_TRACING_ENABLED: "false"  # Disable in CI
  MUDIPU_STORAGE_DIRECTORY: "/tmp/ci-traces"
```

## Advanced Configuration

### Per-Session Configuration

```python
from mudipu.context import session_context
from mudipu.config import MudipuConfig

# Custom config for this session only
custom_config = MudipuConfig()
custom_config.storage.format = "msgpack"

with session_context(
    name="custom-session",
    config=custom_config
) as session:
    # This session uses custom config
    pass
```

### Dynamic Configuration

```python
from mudipu.config import get_config
import os

config = get_config()

# Enable tracing only for specific users
config.tracing.enabled = os.getenv("USER") in ["developer1", "developer2"]

# Adjust sampling based on load
import psutil
cpu_usage = psutil.cpu_percent()
config.tracing.sample_rate = 0.01 if cpu_usage > 80 else 1.0
```

### Configuration Validation

```python
from mudipu.config import MudipuConfig
from pydantic import ValidationError

try:
    config = MudipuConfig.from_yaml("config.yaml")
except ValidationError as e:
    print(f"Invalid configuration: {e}")
```

## Troubleshooting

### Config Not Loading

**Check file path:**

```python
from pathlib import Path

config_path = Path("mudipu.yaml")
print(f"Exists: {config_path.exists()}")
print(f"Absolute: {config_path.absolute()}")
```

**Check YAML syntax:**

```bash
python -c "import yaml; yaml.safe_load(open('mudipu.yaml'))"
```

### Environment Variables Not Working

**Verify they're set:**

```python
import os
print(os.environ.get("MUDIPU_STORAGE_DIRECTORY"))
```

**Check precedence:**

Environment variables override YAML. If both are set, env vars win.

### Permission Issues

```bash
# Check directory permissions
ls -la ./mudipu-traces

# Fix permissions
chmod 755 ./mudipu-traces
```

## See Also

- [Getting Started Guide](getting-started.md)
- [API Reference](api-reference.md)
- [CLI Reference](cli-reference.md)
