"""
Summary generation for trace analysis.
"""
from typing import Optional
from pathlib import Path

from mudipu.models import Session
from mudipu.analyzer.analyzer import TraceAnalyzer
from mudipu.utils.time import format_duration


class SummaryGenerator:
    """
    Generate human-readable summaries of traces.
    """
    
    def __init__(self, session: Session):
        """
        Initialize summary generator.
        
        Args:
            session: Session to summarize
        """
        self.session = session
        self.analyzer = TraceAnalyzer(session)
    
    def generate_text_summary(self) -> str:
        """
        Generate a text summary of the session.
        
        Returns:
            Text summary
        """
        stats = self.analyzer.get_statistics()
        
        lines = [
            "=" * 60,
            f"Mudipu Trace Summary: {self.session.name or 'Unnamed Session'}",
            "=" * 60,
            "",
            f"Session ID: {self.session.session_id}",
            f"Created: {self.session.created_at}",
            "",
            "📊 Statistics:",
            f"  • Total Turns: {stats['turn_count']}",
            f"  • Total Duration: {format_duration(stats['total_duration_ms'])}",
            f"  • Average Duration: {format_duration(stats['avg_duration_ms'])}",
            f"  • Total Tokens: {stats['total_tokens']:,}",
            f"  • Average Tokens/Turn: {stats['avg_tokens_per_turn']:.1f}",
            "",
        ]
        
        # Model usage
        if stats['model_usage']:
            lines.append("🤖 Model Usage:")
            for model, count in stats['model_usage'].items():
                lines.append(f"  • {model}: {count} turns")
            lines.append("")
        
        # Tool usage
        if stats['tool_call_count'] > 0:
            lines.append(f"🔧 Tool Calls: {stats['tool_call_count']}")
            for tool, count in stats['tool_usage'].items():
                lines.append(f"  • {tool}: {count} calls")
            lines.append("")
        
        # Token breakdown
        token_breakdown = stats['token_breakdown']
        lines.extend([
            "💰 Token Breakdown:",
            f"  • Prompt Tokens: {token_breakdown['prompt_tokens']:,}",
            f"  • Completion Tokens: {token_breakdown['completion_tokens']:,}",
            f"  • Total Tokens: {token_breakdown['total_tokens']:,}",
            "",
        ])
        
        # Cost estimate
        costs = self.analyzer.get_cost_estimate()
        if costs:
            lines.append("💵 Estimated Cost:")
            for model, cost in costs.items():
                if model != "total":
                    lines.append(f"  • {model}: ${cost:.4f}")
            lines.append(f"  • Total: ${costs.get('total', 0):.4f}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def generate_markdown_summary(self) -> str:
        """
        Generate a Markdown summary of the session.
        
        Returns:
            Markdown summary
        """
        stats = self.analyzer.get_statistics()
        
        lines = [
            f"# Mudipu Trace Summary: {self.session.name or 'Unnamed Session'}",
            "",
            f"**Session ID:** `{self.session.session_id}`  ",
            f"**Created:** {self.session.created_at}",
            "",
            "## 📊 Statistics",
            "",
            f"- **Total Turns:** {stats['turn_count']}",
            f"- **Total Duration:** {format_duration(stats['total_duration_ms'])}",
            f"- **Average Duration:** {format_duration(stats['avg_duration_ms'])}",
            f"- **Total Tokens:** {stats['total_tokens']:,}",
            f"- **Average Tokens/Turn:** {stats['avg_tokens_per_turn']:.1f}",
            "",
        ]
        
        # Model usage
        if stats['model_usage']:
            lines.append("## 🤖 Model Usage")
            lines.append("")
            for model, count in stats['model_usage'].items():
                lines.append(f"- **{model}:** {count} turns")
            lines.append("")
        
        # Tool usage
        if stats['tool_call_count'] > 0:
            lines.append(f"## 🔧 Tool Calls ({stats['tool_call_count']} total)")
            lines.append("")
            for tool, count in stats['tool_usage'].items():
                lines.append(f"- **{tool}:** {count} calls")
            lines.append("")
        
        # Token breakdown
        token_breakdown = stats['token_breakdown']
        lines.extend([
            "## 💰 Token Breakdown",
            "",
            f"- **Prompt Tokens:** {token_breakdown['prompt_tokens']:,}",
            f"- **Completion Tokens:** {token_breakdown['completion_tokens']:,}",
            f"- **Total Tokens:** {token_breakdown['total_tokens']:,}",
            "",
        ])
        
        # Cost estimate
        costs = self.analyzer.get_cost_estimate()
        if costs:
            lines.append("## 💵 Estimated Cost")
            lines.append("")
            for model, cost in costs.items():
                if model != "total":
                    lines.append(f"- **{model}:** ${cost:.4f}")
            lines.append(f"- **Total:** ${costs.get('total', 0):.4f}")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_summary(self, output_path: Path, format: str = "text") -> None:
        """
        Save summary to file.
        
        Args:
            output_path: Path to save summary
            format: Format ('text' or 'markdown')
        """
        if format == "markdown":
            content = self.generate_markdown_summary()
        else:
            content = self.generate_text_summary()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
