# Changelog

All notable changes to the Mudipu Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **GitHub Actions publish workflow**: Automated PyPI publishing via OIDC Trusted Publishing on version tag push (`v*.*.*`) or manual trigger
- **Platform extra (`mudipu[platform]`)**: `mudipu-packages` dependency now correctly scoped to the `platform` extra only; removed from `all` extra to prevent resolution failures for users without private registry access

### Changed
- **`PlatformExporter`**: Removed NATS transport from the SDK layer. The exporter now POSTs `TraceEvent` JSON payloads to the Mudipu platform gateway HTTP endpoint (`/ingest/turn`). The gateway owns NATS routing internally, keeping the SDK dependency-free of NATS
- **`mudipu[all]` extra**: No longer includes `mudipu-packages` — install `mudipu[platform]` explicitly when platform export is needed

## [1.0.0] - 2026-03-29

### Added
- **Health Metrics System**: Complete context health analysis with 12 metrics (relevance, duplicates, saturation, loops, novelty, growth rate, drift, progress, effectiveness)
- **CLI Enhancements**: Progress spinners and real-time status updates during analysis
- **CLI Help Text**: Comprehensive help text and examples for all commands
- **Health Command**: New `mudipu health` command with visualization support, custom goals, and configurable thresholds
- **Progress Callbacks**: Real-time progress feedback throughout health analysis pipeline
- **Comprehensive Documentation**:
  - Getting Started Guide (300+ lines)
  - Health Metrics Documentation (300+ lines with formulas and interpretations)
  - API Reference (complete API documentation)
  - Configuration Guide (all config methods and options)
  - CLI Reference (all commands with examples)
  - Contributing Guide (simplified, friendly)
- **Comprehensive Test Suite**:
  - Health analyzer tests (400+ lines, 30+ test methods)
  - CLI tests (all commands)
  - Decorator tests (session, LLM, tool tracing)
  - Model tests (Pydantic validation and serialization)
  - Configuration tests (YAML, env vars, defaults)
- **OSS Release Checklist**: Complete preparation guide with 100+ checklist items
- **Market-Ready README**: Professional README with badges, quick start, and feature highlights
- **Visualization**: Health metrics visualization with matplotlib charts

### Changed
- **CLI Interface**: Enhanced all command help text with detailed examples
- **Model Loading**: Suppressed warnings during sentence-transformer model loading for cleaner output
- **Health Analysis**: Configurable threshold parameter (default 0.5) for health scoring
- **Documentation Structure**: Moved to production-ready documentation format

### Fixed
- **User Experience**: Added progress indicators to prevent perceived hangs during long operations
- **CLI Usability**: Improved help text clarity and accessibility for all commands

### Performance
- **Embeddings Caching**: Optional caching for faster repeated health analysis

## [0.1.0] - 2026-03-20

### Added
- Initial release of Mudipu Python SDK
