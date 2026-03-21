"""
Analyzer for trace sessions.

Provides insights and statistics about LLM usage.
"""
from typing import Optional, Any
from pathlib import Path
from collections import defaultdict

from mudipu.models import Session, BaseTurn as Turn


class TraceAnalyzer:
    """
    Analyze trace sessions for insights and statistics.
    """
    
    def __init__(self, session: Session):
        """
        Initialize analyzer.
        
        Args:
            session: Session to analyze
        """
        self.session = session
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive statistics about the session.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "session_id": str(self.session.session_id),
            "name": self.session.name,
            "turn_count": self.session.turn_count,
            "total_duration_ms": self.session.total_duration_ms,
            "total_tokens": self.session.total_tokens,
            "avg_duration_ms": self._avg_duration(),
            "avg_tokens_per_turn": self._avg_tokens(),
            "model_usage": self._model_usage(),
            "tool_call_count": self._tool_call_count(),
            "tool_usage": self._tool_usage(),
            "message_breakdown": self._message_breakdown(),
            "token_breakdown": self._token_breakdown(),
        }
        
        return stats
    
    def _avg_duration(self) -> float:
        """Calculate average turn duration."""
        if self.session.turn_count == 0:
            return 0.0
        return self.session.total_duration_ms / self.session.turn_count
    
    def _avg_tokens(self) -> float:
        """Calculate average tokens per turn."""
        if self.session.turn_count == 0:
            return 0.0
        return self.session.total_tokens / self.session.turn_count
    
    def _model_usage(self) -> dict[str, int]:
        """Count usage by model."""
        usage = defaultdict(int)
        for turn in self.session.turns:
            if turn.model:
                usage[turn.model] += 1
        return dict(usage)
    
    def _tool_call_count(self) -> int:
        """Count total tool calls."""
        return sum(len(turn.tool_calls_detected) for turn in self.session.turns)
    
    def _tool_usage(self) -> dict[str, int]:
        """Count usage by tool."""
        usage = defaultdict(int)
        for turn in self.session.turns:
            for tool_call in turn.tool_calls_detected:
                if tool_call.function_name:
                    usage[tool_call.function_name] += 1
        return dict(usage)
    
    def _message_breakdown(self) -> dict[str, int]:
        """Count messages by role."""
        breakdown = defaultdict(int)
        for turn in self.session.turns:
            for msg in turn.request_messages:
                role = msg.get("role", "unknown")
                breakdown[role] += 1
        return dict(breakdown)
    
    def _token_breakdown(self) -> dict[str, int]:
        """Break down token usage."""
        breakdown = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        
        for turn in self.session.turns:
            if turn.usage:
                breakdown["prompt_tokens"] += turn.usage.get("prompt_tokens", 0)
                breakdown["completion_tokens"] += turn.usage.get("completion_tokens", 0)
                breakdown["total_tokens"] += turn.usage.get("total_tokens", 0)
        
        return breakdown
    
    def get_cost_estimate(self, pricing: Optional[dict[str, dict]] = None) -> dict[str, float]:
        """
        Estimate costs based on token usage and pricing.
        
        Args:
            pricing: Pricing dictionary (model -> {prompt_per_1k, completion_per_1k})
            
        Returns:
            Cost breakdown by model
        """
        if pricing is None:
            # Default pricing (example rates in USD)
            pricing = {
                "gpt-4": {"prompt_per_1k": 0.03, "completion_per_1k": 0.06},
                "gpt-4-turbo": {"prompt_per_1k": 0.01, "completion_per_1k": 0.03},
                "gpt-3.5-turbo": {"prompt_per_1k": 0.0015, "completion_per_1k": 0.002},
            }
        
        costs: dict[str, float] = {}
        total_cost = 0.0
        
        for turn in self.session.turns:
            if not turn.model or not turn.usage:
                continue
            
            if turn.model not in pricing:
                continue
            
            model_pricing = pricing[turn.model]
            prompt_tokens = turn.usage.get("prompt_tokens", 0)
            completion_tokens = turn.usage.get("completion_tokens", 0)
            
            turn_cost = (
                (prompt_tokens / 1000) * model_pricing["prompt_per_1k"] +
                (completion_tokens / 1000) * model_pricing["completion_per_1k"]
            )
            
            costs[turn.model] = costs.get(turn.model, 0.0) + turn_cost
            total_cost += turn_cost
        
        costs["total"] = total_cost
        return costs
    
    def find_slow_turns(self, threshold_ms: float = 1000.0) -> list[Turn]:
        """
        Find turns that took longer than threshold.
        
        Args:
            threshold_ms: Duration threshold in milliseconds
            
        Returns:
            List of slow turns
        """
        return [
            turn for turn in self.session.turns
            if turn.duration_ms and turn.duration_ms > threshold_ms
        ]
    
    def find_expensive_turns(self, threshold_tokens: int = 1000) -> list[Turn]:
        """
        Find turns that used more than threshold tokens.
        
        Args:
            threshold_tokens: Token threshold
            
        Returns:
            List of expensive turns
        """
        result = []
        for turn in self.session.turns:
            if turn.usage:
                total = turn.usage.get("total_tokens", 0)
                if total > threshold_tokens:
                    result.append(turn)
        return result
