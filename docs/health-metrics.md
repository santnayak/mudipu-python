# Context Health Metrics

> **⚠️ ALPHA VERSION - WORK IN PROGRESS ⚠️**
> 
> **These metrics are currently in active development and validation.**
> 
> - ⚠️ **Use with caution** - Metrics are not yet fully validated
> - 🔬 **Validation ongoing** - Results will be published soon
> - ⚖️ **Equal weighting** - All metric weights are currently equal (will be adjusted based on evaluation results)
> - 📊 **Experimental status** - Formulas and thresholds may change in future releases
> 
> For research use and early feedback only. Not recommended for production decision-making until validation is complete.

---

**Detect inefficiencies, loops, and drift in your AI agents**

Context health metrics help you understand **why** your agent succeeded or failed, not just **what** it did.

## Overview

Mudipu analyzes agent traces to compute quality scores across two levels:

1. **Per-Turn Metrics**: Quality of individual LLM interactions
2. **Session Metrics**: Overall agent performance

> **Note**: Current implementation uses **equal weighting** across all factors. Weights will be optimized based on ongoing validation studies and empirical results.

## Installation

Health metrics require additional dependencies:

```bash
pip install mudipu[health]
```

## Quick Example

```bash
# Analyze a trace
mudipu health trace.json

# With visualization
mudipu health trace.json --visualize

# Save results
mudipu health trace.json --save-json metrics.json
```

## Per-Turn Metrics

### Relevance Score (0.0 - 1.0)

**What it measures**: How on-topic is the current turn's context?

**Formula**: Cosine similarity between goal embedding and context embeddings

**Research basis**: Semantic similarity using sentence embeddings has been shown to correlate with human relevance judgments (Reimers & Gurevych, 2019)[^1].

**Interpretation**:
- `>= 0.7`: Highly relevant ✅
- `0.5 - 0.7`: Moderately relevant 🟡
- `< 0.5`: Off-topic ❌

> ⚠️ **Caution**: Thresholds are preliminary and based on limited validation data.

**Example**:
```python
Goal: "Find the weather in Paris"
Turn 3 context: "According to Wikipedia, Paris has a population of..."
→ Relevance: 0.45 (drifted from weather to demographics)
```

### Duplicate Ratio (0.0 - 1.0)

**What it measures**: How much repeated/redundant content exists?

**Formula**: Average pairwise semantic similarity of context items

**Research basis**: Redundancy detection via semantic similarity is a common technique in information retrieval and summarization (Carbonell & Goldstein, 1998)[^2].

**Interpretation**:
- `< 0.3`: Minimal duplication ✅
- `0.3 - 0.6`: Moderate redundancy 🟡
- `> 0.6`: High duplication ❌

> ⚠️ **Caution**: Similarity threshold (0.85) is based on preliminary testing and may be adjusted.

**Common causes**:
- RAG retrieving same documents repeatedly
- Agent re-fetching the same tool results
- Circular reasoning in multi-turn conversations

### Saturation Score (0.0 - 1.0)

**What it measures**: Context window pressure

**Formula**: `prompt_tokens / context_limit`

**Research basis**: Context length constraints affect transformer model performance (Liu et al., 2023)[^3]. Token limits vary by model (GPT-4: 128K, Claude: 200K).

**Interpretation**:
- `< 0.5`: Plenty of room ✅
- `0.5 - 0.8`: Getting full 🟡
- `> 0.8`: Near limit ❌

> ⚠️ **Caution**: Default context limit (8192) may not match your model. Configure appropriately.

**Why it matters**: High saturation can lead to:
- Lost context (tokens get truncated)
- Degraded performance
- Increased costs

### Tool Loop Score (0.0 - 1.0)

**What it measures**: Repeated tool calls with similar arguments

**Logic**:
1. Looks back 3 turns
2. Counts repeated tool names
3. Normalizes by window size

**Research basis**: Action repetition patterns in agent systems indicate inefficiency or failure modes (Yao et al., 2023)[^4].

**Interpretation**:
- `0.0`: No loops ✅
- `0.3 - 0.6`: Some repetition 🟡
- `> 0.6`: Stuck in loop ❌

> ⚠️ **Caution**: Lookback window (3 turns) is heuristic-based and under evaluation.

**Example**:
```
Turn 1: web_search("weather Paris")
Turn 2: web_search("weather Paris")  ← Loop detected!
Turn 3: web_search("weather Paris")  ← Still looping!
Loop score: 0.67
```

### Novelty Score (0.0 - 1.0)

**What it measures**: Is this turn adding new information?

**Formula**: `1.0 - max_similarity(current_output, all_previous_outputs)`

**Research basis**: Information gain and novelty detection in conversational systems (Zhang et al., 2020)[^5].

**Interpretation**:
- `>= 0.7`: Highly novel ✅
- `0.4 - 0.7`: Some progress 🟡
- `< 0.4`: Repetitive ❌

> ⚠️ **Caution**: Novelty thresholds are preliminary and may not generalize across all task types.

**Why it matters**: Low novelty often indicates:
- Agent is stuck
- Same answer being regenerated
- No progress toward goal

### Turn Health Score (Combined)

> ⚠️ **EXPERIMENTAL WEIGHTS** - Currently using **equal weighting** (0.20 each). These will be optimized based on validation results.

**Formula** (current implementation):
```python
health = (
    0.20 * relevance +
    0.20 * (1 - duplicate_ratio) +
    0.20 * (1 - saturation) +
    0.20 * (1 - tool_loop) +
    0.20 * novelty
)
```

**Planned approach**: Weights will be determined through:
- Correlation with human quality ratings
- A/B testing on diverse agent traces
- Optimization for different task types

**Current equal weighting rationale**: Until validation is complete, we avoid introducing bias by assigning equal importance to all factors.

## Session-Level Metrics

### Context Growth Rate (tokens/turn)

**What it measures**: How fast is context expanding?

**Formula**: Linear regression slope of prompt tokens over turns

**Research basis**: Context accumulation patterns affect long-running agent performance (Shen et al., 2023)[^6].

**Interpretation**:
- `0-50`: Slow growth ✅
- `50-100`: Moderate growth 🟡
- `> 100`: Rapid growth ❌

> ⚠️ **Caution**: Growth rate thresholds are task-dependent and require further validation.

**Example**:
```
Turn 1: 400 tokens
Turn 2: 550 tokens (+150)
Turn 3: 680 tokens (+130)
Turn 4: 850 tokens (+170)
→ Growth rate: ~58 tokens/turn
```

### Drift Score (0.0 - 1.0)

**What it measures**: Goal misalignment over time

**Formula**: `early_relevance - late_relevance`

**Research basis**: Goal drift in multi-turn interactions is a known challenge in conversational AI (Mehri & Eskenazi, 2020)[^7].

**Interpretation**:
- `< 0.2`: Minimal drift ✅
- `0.2 - 0.4`: Some drift 🟡
- `> 0.4`: Significant drift ❌

> ⚠️ **Caution**: Early/late turn split is currently fixed at 50%. May need adjustment for different session lengths.

**Why it happens**:
- Agent follows tangent
- Context window fills with irrelevant info
- Multi-hop reasoning loses original goal

### Loop Score (0.0 - 1.0)

**What it measures**: Average tool looping across all turns

**Formula**: `mean(all_turn_loop_scores)`

**Interpretation**:
- `< 0.3`: Efficient ✅
- `0.3 - 0.6`: Some loops 🟡
- `> 0.6`: Inefficient ❌

### Progress Score (0.0 - 1.0)

**What it measures**: Ratio of productive turns

**Formula**: `productive_turns / total_turns`
- Productive = novelty > 0.5

**Interpretation**:
- `>= 0.7`: Most turns useful ✅
- `0.4 - 0.7`: Mixed efficiency 🟡
- `< 0.4`: Many wasted turns

 ❌

### Effectiveness Score (0.0 - 1.0)

**What it measures**: Did the session end with a complete answer?

**Heuristic**:
- Ended with tool calls: `0.3` (incomplete)
- Short answer (< 10 words): `0.4`
- Medium answer (10-50 words): `0.7`
- Long answer (> 50 words): `0.9`

**Research basis**: Answer completeness heuristics are common in QA systems (Rajpurkar et al., 2016)[^8].

**Interpretation**:
- `>= 0.7`: Likely complete ✅
- `0.4 - 0.7`: Partial answer 🟡
- `< 0.4`: Incomplete ❌

> ⚠️ **Caution**: This is a **rough heuristic**. Word count thresholds are approximate and task-dependent.

### Overall Health Score (Combined)

> ⚠️ **EXPERIMENTAL WEIGHTS** - Currently using **equal weighting** (0.20 each). These will be optimized based on validation results.

**Formula** (current implementation):
```python
overall_health = (
    0.20 * (1 - abs(growth_rate) / 100) +
    0.20 * (1 - drift) +
    0.20 * (1 - loop) +
    0.20 * progress +
    0.20 * effectiveness
)
```

**Planned approach**: Weights will be empirically derived from:
- Correlation studies with human expert ratings
- Analysis of successful vs. failed agent runs
- Task-specific optimization

**Why equal weights now**: We avoid premature optimization until sufficient validation data is collected.

## Using Health Metrics

### Via CLI

```bash
# Basic analysis
mudipu health trace.json

# With custom threshold
mudipu health trace.json --threshold 0.6

# With goal specification
mudipu health trace.json --goal "Find weather in Paris"

# Generate visualization
mudipu health trace.json --visualize

# Save to JSON
mudipu health trace.json --save-json output.json
```

### Programmatically

```python
from mudipu.analyzer import TraceAnalyzer
from mudipu.exporters import JSONExporter

# Load trace
exporter = JSONExporter()
session = exporter.load("trace.json")

# Analyze health
analyzer = TraceAnalyzer(session)
metrics = analyzer.get_health_metrics(
    goal="Find weather in Paris",
    include_viz=True
)

# Access results
for turn_metric in metrics["per_turn"]:
    print(f"Turn {turn_metric['turn_number']}: {turn_metric['health_score']:.3f}")

session_health = metrics["session"]["overall_health"]
print(f"Overall health: {session_health:.3f}")
```

### With Custom Progress Callback

```python
def progress_callback(message: str):
    print(f"[STATUS] {message}")

metrics = analyzer.get_health_metrics(
    progress_callback=progress_callback
)
```

## Visualization

Enable visualization to generate 4-panel charts:

```bash
mudipu health trace.json --visualize
```

**Chart 1: Context Growth**
- X-axis: Turn number
- Y-axis: Prompt tokens
- Annotations: Tool calls

**Chart 2: Health Trends**
- Lines for overall health, relevance, novelty
- Threshold line at 0.5

**Chart 3: Component Breakdown**
- All 5 metric components over time

**Chart 4: Session Summary**
- Bar chart of session-level scores

## Interpreting Results

### Healthy Session Example

```
Overall Health: 0.85 🟢 HEALTHY

├─ Context Growth: +42 tokens/turn ✅
├─ Drift Score: 0.12 ✅
├─ Loop Score: 0.15 ✅
├─ Progress: 0.83 ✅
└─ Effectiveness: 0.90 ✅
```

**What this means**: Agent stayed on topic, made steady progress, minimal loops, complete answer.

### Unhealthy Session Example

```
Overall Health: 0.43 🔴 UNHEALTHY

├─ Context Growth: +145 tokens/turn ❌
├─ Drift Score: 0.68 ❌
├─ Loop Score: 0.72 ❌
├─ Progress: 0.33 ❌
└─ Effectiveness: 0.40 ❌

⚠️  Tool loops detected
⚠️  Significant goal drift detected
⚠️  Rapid context growth (risk of saturation)
⚠️  Low effectiveness (verify completion)
```

**What this means**: Agent got stuck in loops, drifted from goal, wasted turns, incomplete answer.

## Advanced Configuration

### Custom Context Limit

```python
from mudipu.analyzer.health import ContextHealthAnalyzer

analyzer = ContextHealthAnalyzer(
    session,
    goal="Your goal here",
    assumed_context_limit=128000  # GPT-4 Turbo limit
)
```

### Custom Embedding Model

```python
analyzer = ContextHealthAnalyzer(
    session,
    embedding_model="all-MiniLM-L6-v2"  # Default
    # Or: "all-mpnet-base-v2" for higher quality
)
```

## Methodology

### Semantic Similarity

We use [sentence-transformers](https://www.sbert.net/) for computing embeddings:

- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Similarity**: Cosine similarity
- **Range**: -1 (opposite) to +1 (identical)
- **Scaled**: Mapped to 0.0 - 1.0 for scores

### Statistical Methods

- **Growth rate**: Linear regression (scikit-learn)
- **Similarity threshold**: 0.85 for duplicates
- **Lookback window**: 3 turns for loop detection

## Validation & Research Status

> ⚠️ **ONGOING VALIDATION** - Results are preliminary and subject to change.



### How You Can Help

- Feedback on metric behavior in your use cases
- Contributions of anonymized trace data for validation
- Suggestions for metric improvements

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

## Limitations & Known Issues

> ⚠️ **Important**: These metrics are experimental and have known limitations.


### Known Edge Cases

- **Long-running sessions**: Metrics may behave differently beyond 20+ turns
- **Agentic workflows**: Complex multi-agent systems not yet tested

### Planned Improvements

- Task-specific metric variants
- Learned weights from validation data
- Better effectiveness heuristics
- Support for multi-modal content
- Confidence intervals for scores

## FAQ

### Q: Are these metrics production-ready?

**A**: **No, not yet.** They are in active development and validation. Use for research, development, and early feedback only. Do not make critical production decisions based on these metrics until validation is complete.

### Q: Do I need a goal for health metrics?

**A**: No, but relevance/drift scores will be less meaningful. You can still get loop, novelty, and saturation metrics without a goal.

### Q: Can I tune the weights?

**A**: Not currently. Weights are fixed at equal values (0.20 each) pending validation studies. Custom weighting will come in future releases after empirical optimization.

### Q: How much overhead does this add?

**A**: Minimal during tracing (decorators are lightweight). Analysis happens post-hoc and takes ~1-3 seconds per trace. Embedding computation is the main cost.

### Q: Can I use this in production?

**A**: ⚠️ **Use with caution**. Health metrics are computed from saved traces, not during agent execution, so they don't affect runtime performance. However, the metrics themselves are experimental and not fully validated. Recommended for monitoring and debugging, not for automated decision-making.

### Q: Why are all weights equal?

**A**: Until we complete validation studies correlating metrics with human quality judgments and agent success rates, we avoid introducing bias through arbitrary weight assignments. Equal weights will be replaced with empirically-derived values once validation is complete.

### Q: When will validation results be published?

**A**: Don't know yet! probably in Q4 2026.


> ⚠️ **Research use only**: Until validation is complete, use these metrics for research purposes and early feedback, not for production decision-making.

## References

[^1]: Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *Proceedings of EMNLP-IJCNLP 2019*. [arXiv:1908.10084](https://arxiv.org/abs/1908.10084)

[^2]: Carbonell, J., & Goldstein, J. (1998). The use of MMR, diversity-based reranking for reordering documents and producing summaries. *Proceedings of SIGIR 1998*, 335-336.

[^3]: Liu, N. F., et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. *arXiv preprint*. [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)

[^4]: Yao, S., et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*. [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)

[^5]: Zhang, Y., et al. (2020). DIALOGPT: Large-Scale Generative Pre-training for Conversational Response Generation. *ACL 2020*. [arXiv:1911.00536](https://arxiv.org/abs/1911.00536)

[^6]: Shen, Y., et al. (2023). Hugginggpt: Solving ai tasks with chatgpt and its friends in hugging face. *NeurIPS 2023*. [arXiv:2303.17580](https://arxiv.org/abs/2303.17580)

[^7]: Mehri, S., & Eskenazi, M. (2020). USR: An Unsupervised and Reference Free Evaluation Metric for Dialog Generation. *ACL 2020*. [arXiv:2005.00456](https://arxiv.org/abs/2005.00456)

[^8]: Rajpurkar, P., et al. (2016). SQuAD: 100,000+ Questions for Machine Comprehension of Text. *EMNLP 2016*. [arXiv:1606.05250](https://arxiv.org/abs/1606.05250)

---

**Note**: The metrics and methodologies described in this document are **experimental and under active development**. Research references are provided to indicate the theoretical basis for each metric, but the specific implementations in Mudipu are original and require independent validation.

## Next Steps

- [Configuration Guide](./configuration.md) - Customize analysis
- [CLI Reference](./cli-reference.md) - All command options
- [API Reference](./api-reference.md) - Programmatic usage
- [Examples](../examples/) - Real-world use cases

