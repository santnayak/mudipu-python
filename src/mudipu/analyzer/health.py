"""
Context health analysis for agent traces.

Provides metrics to assess the quality and efficiency of LLM agent interactions.
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
import numpy as np
import os
import warnings

from mudipu.models import Session, BaseTurn

# Optional dependencies - loaded on first use
_sentence_transformer = None
_sklearn_available = False


def _get_sentence_transformer():
    """Lazy load sentence transformer."""
    global _sentence_transformer
    if _sentence_transformer is None:
        try:
            # Suppress HuggingFace warnings and progress bars
            os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            
            # Suppress transformers warnings
            warnings.filterwarnings('ignore', category=FutureWarning)
            warnings.filterwarnings('ignore', category=UserWarning)
            
            # Set logging level to ERROR to suppress INFO messages
            import logging
            logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
            logging.getLogger('transformers').setLevel(logging.ERROR)
            
            from sentence_transformers import SentenceTransformer
            _sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2", show_progress_bar=False)
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for health metrics. "
                "Install with: pip install mudipu[health]"
            )
    return _sentence_transformer


def _check_sklearn():
    """Check if sklearn is available."""
    global _sklearn_available
    try:
        import sklearn
        _sklearn_available = True
    except ImportError:
        _sklearn_available = False
    return _sklearn_available


@dataclass
class TurnHealthMetrics:
    """Health metrics for a single turn."""
    turn_number: int
    relevance_score: float
    duplicate_ratio: float
    saturation_score: float
    tool_loop_score: float
    novelty_score: float
    health_score: float
    details: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SessionHealthMetrics:
    """Health metrics for an entire session."""
    session_id: str
    turns_analyzed: int
    context_growth_rate: float
    drift_score: float
    loop_score: float
    progress_score: float
    effectiveness_score: float
    overall_health: float
    details: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class HealthAnalysis:
    """Complete health analysis results."""
    per_turn: List[TurnHealthMetrics]
    session: SessionHealthMetrics
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "per_turn": [t.to_dict() for t in self.per_turn],
            "session": self.session.to_dict()
        }


class ContextHealthAnalyzer:
    """
    Analyze context quality in agent traces.
    
    Computes per-turn and session-level health metrics including:
    - Relevance: How on-topic is the context?
    - Redundancy: How much repeated content?
    - Saturation: Context window pressure
    - Tool loops: Inefficient repeated calls
    - Drift: Losing track of goal
    - Novelty: Is progress being made?
    """
    
    def __init__(
        self,
        session: Session,
        goal: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        assumed_context_limit: int = 8192,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize health analyzer.
        
        Args:
            session: Trace session to analyze
            goal: User's goal/objective for relevance scoring (optional)
            embedding_model: Sentence transformer model name
            assumed_context_limit: Context window size in tokens
            progress_callback: Optional callback function for progress updates
        """
        self.session = session
        self.embedding_model_name = embedding_model
        self.assumed_context_limit = assumed_context_limit
        self.progress_callback = progress_callback
        
        # Set goal from parameter or try to extract from session metadata
        if goal:
            self.goal = goal
        elif session.metadata:
            self.goal = session.metadata.get("user_input", "")
        else:
            self.goal = ""
        
        # Lazy load model
        self._model = None
    
    @property
    def model(self):
        """Get sentence transformer model (lazy loaded)."""
        if self._model is None:
            if self.progress_callback:
                self.progress_callback("Loading sentence transformer model...")
            self._model = _get_sentence_transformer()
        return self._model
    
    # Utility methods
    
    @staticmethod
    def _cosine_similarity_matrix(vectors: np.ndarray) -> np.ndarray:
        """Compute pairwise cosine similarity."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.clip(norms, 1e-12, None)
        normalized = vectors / norms
        return normalized @ normalized.T
    
    @staticmethod
    def _clip_01(value: float) -> float:
        """Clip value to [0, 1] range."""
        return float(max(0.0, min(1.0, value)))
    
    # Per-turn metric computations
    
    def _compute_turn_relevance(self, turn: BaseTurn) -> float:
        """
        Compute relevance score for a turn.
        
        Measures semantic similarity between turn context and session goal.
        """
        if not self.goal.strip():
            return 0.0
        
        # Extract text from turn messages
        turn_texts = []
        for msg in turn.request_messages:
            content = msg.get("content", "")
            if content and isinstance(content, str):
                turn_texts.append(content)
        
        if not turn_texts:
            return 0.0
        
        try:
            # Compute embeddings
            texts = [self.goal] + turn_texts
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # Similarity of goal with turn context
            sim_matrix = self._cosine_similarity_matrix(embeddings)
            goal_to_context = sim_matrix[0, 1:]
            avg_similarity = float(np.mean(goal_to_context))
            
            # Scale from [-1, 1] to [0, 1]
            return self._clip_01((avg_similarity + 1.0) / 2.0)
        except Exception:
            # Fallback if embedding fails
            return 0.5
    
    def _compute_turn_duplicate_ratio(self, turn: BaseTurn) -> float:
        """
        Compute redundancy within turn context.
        
        Measures how much repeated/similar content exists in the turn.
        """
        # Extract all text snippets from turn
        texts = []
        
        # From messages
        for msg in turn.request_messages:
            content = msg.get("content", "")
            if content and isinstance(content, str) and len(content.strip()) > 0:
                texts.append(content)
        
        # From tool results (if available)
        if hasattr(turn, "tool_executions") and turn.tool_executions:
            for tool_exec in turn.tool_executions:
                if isinstance(tool_exec, dict) and tool_exec.get("result"):
                    result = str(tool_exec["result"])
                    if len(result.strip()) > 0:
                        texts.append(result)
        
        if len(texts) < 2:
            return 0.0
        
        try:
            # Compute pairwise similarities
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            sim_matrix = self._cosine_similarity_matrix(embeddings)
            
            # Upper triangle (avoid self-similarity)
            n = len(texts)
            similarities = []
            for i in range(n):
                for j in range(i + 1, n):
                    similarities.append(sim_matrix[i, j])
            
            if not similarities:
                return 0.0
            
            avg_similarity = float(np.mean(similarities))
            return self._clip_01((avg_similarity + 1.0) / 2.0)
        except Exception:
            return 0.0
    
    def _compute_turn_saturation(self, turn: BaseTurn) -> float:
        """
        Compute context window saturation.
        
        Measures how much of the context window is being used.
        """
        if not turn.usage:
            return 0.0
        
        prompt_tokens = turn.usage.get("prompt_tokens", 0)
        raw_saturation = prompt_tokens / self.assumed_context_limit
        return self._clip_01(raw_saturation)
    
    def _compute_turn_tool_loop(self, turn_idx: int) -> float:
        """
        Detect tool loop patterns.
        
        Checks if the same tools are being called repeatedly.
        """
        if turn_idx == 0:
            return 0.0
        
        current_turn = self.session.turns[turn_idx]
        
        # Get last 3 turns for comparison
        lookback = min(3, turn_idx)
        previous_turns = self.session.turns[max(0, turn_idx - lookback):turn_idx]
        
        if not current_turn.tool_calls_detected:
            return 0.0
        
        current_tools = [tc.function_name for tc in current_turn.tool_calls_detected if tc.function_name]
        
        if not current_tools:
            return 0.0
        
        # Count repeated tool names
        loop_score = 0.0
        for prev_turn in previous_turns:
            if not prev_turn.tool_calls_detected:
                continue
            
            prev_tools = [tc.function_name for tc in prev_turn.tool_calls_detected if tc.function_name]
            common_tools = set(current_tools) & set(prev_tools)
            
            if common_tools:
                loop_score += len(common_tools) / max(len(current_tools), 1)
        
        # Normalize by lookback window
        if lookback > 0:
            loop_score /= lookback
        
        return self._clip_01(loop_score)
    
    def _compute_turn_novelty(self, turn_idx: int) -> float:
        """
        Compute how much new information this turn added.
        
        Low novelty indicates possible loop or stall.
        """
        if turn_idx == 0:
            return 1.0  # First turn is always novel
        
        current_turn = self.session.turns[turn_idx]
        previous_turns = self.session.turns[:turn_idx]
        
        # Extract current turn output
        current_output = ""
        if current_turn.response_message:
            current_output = current_turn.response_message.get("content", "")
        
        if not current_output or not isinstance(current_output, str) or not current_output.strip():
            # No content - check tool results instead
            if hasattr(current_turn, "tool_executions") and current_turn.tool_executions:
                tool_results = []
                for tool_exec in current_turn.tool_executions:
                    if isinstance(tool_exec, dict) and tool_exec.get("result"):
                        tool_results.append(str(tool_exec["result"]))
                current_output = " ".join(tool_results)
            
            if not current_output.strip():
                return 0.5  # Neutral if no content
        
        # Extract previous outputs
        previous_outputs = []
        for turn in previous_turns:
            if turn.response_message and turn.response_message.get("content"):
                content = turn.response_message["content"]
                if isinstance(content, str) and content.strip():
                    previous_outputs.append(content)
        
        if not previous_outputs:
            return 1.0
        
        try:
            # Compute similarity with previous outputs
            all_outputs = previous_outputs + [current_output]
            embeddings = self.model.encode(all_outputs, convert_to_numpy=True)
            
            current_vec = embeddings[-1:]
            previous_vecs = embeddings[:-1]
            
            # Max similarity with any previous turn
            combined = np.vstack([current_vec, previous_vecs])
            sim_matrix = self._cosine_similarity_matrix(combined)
            max_similarity = float(np.max(sim_matrix[0, 1:]))
            
            # Novelty is inverse of similarity
            novelty = 1.0 - self._clip_01((max_similarity + 1.0) / 2.0)
            return novelty
        except Exception:
            return 0.5
    
    def analyze_turn(self, turn_idx: int) -> TurnHealthMetrics:
        """
        Compute health metrics for a single turn.
        
        Args:
            turn_idx: Index of turn in session
            
        Returns:
            TurnHealthMetrics with all computed scores
        """
        turn = self.session.turns[turn_idx]
        
        relevance = self._compute_turn_relevance(turn)
        duplicate_ratio = self._compute_turn_duplicate_ratio(turn)
        saturation = self._compute_turn_saturation(turn)
        tool_loop = self._compute_turn_tool_loop(turn_idx)
        novelty = self._compute_turn_novelty(turn_idx)
        
        # Combined health score (weighted average)
        health = (
            0.3 * relevance +
            0.2 * (1.0 - duplicate_ratio) +
            0.1 * (1.0 - saturation) +
            0.2 * (1.0 - tool_loop) +
            0.2 * novelty
        )
        
        return TurnHealthMetrics(
            turn_number=turn.turn_number,
            relevance_score=round(relevance, 4),
            duplicate_ratio=round(duplicate_ratio, 4),
            saturation_score=round(saturation, 4),
            tool_loop_score=round(tool_loop, 4),
            novelty_score=round(novelty, 4),
            health_score=round(self._clip_01(health), 4),
            details={
                "prompt_tokens": turn.usage.get("prompt_tokens", 0) if turn.usage else 0,
                "tool_count": len(turn.tool_calls_detected) if turn.tool_calls_detected else 0,
            }
        )
    
    # Session-level metric computations
    
    def _compute_context_growth_rate(self) -> float:
        """
        Calculate average token growth per turn.
        
        Uses linear regression if sklearn available, otherwise simple average.
        """
        if len(self.session.turns) < 2:
            return 0.0
        
        token_counts = []
        for turn in self.session.turns:
            if turn.usage:
                token_counts.append(turn.usage.get("prompt_tokens", 0))
        
        if len(token_counts) < 2:
            return 0.0
        
        # Try sklearn linear regression
        if _check_sklearn():
            try:
                from sklearn.linear_model import LinearRegression
                X = np.array(range(len(token_counts))).reshape(-1, 1)
                y = np.array(token_counts)
                model = LinearRegression().fit(X, y)
                return float(model.coef_[0])
            except Exception:
                pass
        
        # Fallback: simple slope
        return (token_counts[-1] - token_counts[0]) / (len(token_counts) - 1)
    
    def _compute_drift_score(self, turn_metrics: List[TurnHealthMetrics]) -> float:
        """
        Compare early vs late turn relevance.
        
        High drift means later turns are less relevant to original goal.
        """
        if len(turn_metrics) < 3:
            return 0.0
        
        # Split into early and late
        split_point = len(turn_metrics) // 2
        early_relevance = np.mean([m.relevance_score for m in turn_metrics[:split_point]])
        late_relevance = np.mean([m.relevance_score for m in turn_metrics[split_point:]])
        
        # Drift is the drop in relevance
        drift = float(early_relevance - late_relevance)
        
        # Normalize to [0, 1] where 0 = no drift, 1 = severe drift
        # Clamp negative drift to 0 (improvement is not drift)
        return self._clip_01(max(0.0, drift))
    
    def _compute_session_loop_score(self, turn_metrics: List[TurnHealthMetrics]) -> float:
        """Aggregate tool loop scores across all turns."""
        if not turn_metrics:
            return 0.0
        
        loop_scores = [m.tool_loop_score for m in turn_metrics]
        return float(np.mean(loop_scores))
    
    def _compute_progress_score(self, turn_metrics: List[TurnHealthMetrics]) -> float:
        """
        Ratio of productive turns (novel information).
        
        Higher score means more turns contributed meaningfully.
        """
        if not turn_metrics:
            return 0.0
        
        productive_turns = sum(1 for m in turn_metrics if m.novelty_score > 0.5)
        return productive_turns / len(turn_metrics)
    
    def _compute_effectiveness_score(self) -> float:
        """
        Did the session end with a complete answer?
        
        Checks if final turn has meaningful content vs tool calls.
        """
        if not self.session.turns:
            return 0.0
        
        last_turn = self.session.turns[-1]
        
        # Check if final turn has content (not tool calls)
        if not last_turn.response_message:
            return 0.0
        
        content = last_turn.response_message.get("content", "")
        has_tool_calls = last_turn.has_tool_calls
        
        if not content or not isinstance(content, str) or not content.strip():
            return 0.0
        
        if has_tool_calls:
            return 0.3  # Ended with tool calls = incomplete
        
        # Heuristic: longer content = more complete
        content_length = len(content.split())
        if content_length < 10:
            return 0.4
        elif content_length < 50:
            return 0.7
        else:
            return 0.9
    
    def analyze_session(self, turn_metrics: List[TurnHealthMetrics]) -> SessionHealthMetrics:
        """
        Compute session-level health metrics.
        
        Args:
            turn_metrics: Pre-computed per-turn metrics
            
        Returns:
            SessionHealthMetrics with aggregated scores
        """
        growth_rate = self._compute_context_growth_rate()
        drift = self._compute_drift_score(turn_metrics)
        loop_score = self._compute_session_loop_score(turn_metrics)
        progress = self._compute_progress_score(turn_metrics)
        effectiveness = self._compute_effectiveness_score()
        
        # Overall session health (weighted combination)
        # Penalize rapid growth, drift, and loops; reward progress and effectiveness
        overall_health = (
            0.15 * (1.0 - min(1.0, abs(growth_rate) / 100)) +  # Penalize rapid growth
            0.25 * (1.0 - drift) +
            0.25 * (1.0 - loop_score) +
            0.20 * progress +
            0.15 * effectiveness
        )
        
        return SessionHealthMetrics(
            session_id=str(self.session.session_id),
            turns_analyzed=len(turn_metrics),
            context_growth_rate=round(growth_rate, 2),
            drift_score=round(drift, 4),
            loop_score=round(loop_score, 4),
            progress_score=round(progress, 4),
            effectiveness_score=round(effectiveness, 4),
            overall_health=round(self._clip_01(overall_health), 4),
            details={
                "total_tokens": self.session.total_tokens,
                "total_duration_ms": self.session.total_duration_ms,
                "session_name": self.session.name,
            }
        )
    
    def get_full_analysis(self) -> HealthAnalysis:
        """
        Return complete health analysis.
        
        Analyzes all turns and computes session-level metrics.
        
        Returns:
            HealthAnalysis with per-turn and session metrics
        """
        # Analyze each turn
        turn_metrics = []
        total_turns = len(self.session.turns)
        
        for i in range(total_turns):
            if self.progress_callback:
                self.progress_callback(f"Analyzing turn {i + 1}/{total_turns}...")
            turn_metrics.append(self.analyze_turn(i))
        
        # Analyze session
        if self.progress_callback:
            self.progress_callback("Computing session-level metrics...")
        session_metrics = self.analyze_session(turn_metrics)
        
        return HealthAnalysis(
            per_turn=turn_metrics,
            session=session_metrics
        )
