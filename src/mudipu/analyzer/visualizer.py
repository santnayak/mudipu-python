"""
Visualization utilities for health metrics.

Generates charts and plots for context health analysis.
"""
from pathlib import Path
from typing import Optional, List
import warnings

from mudipu.models import Session
from mudipu.analyzer.health import HealthAnalysis, TurnHealthMetrics, SessionHealthMetrics

# Suppress matplotlib warnings
warnings.filterwarnings('ignore')


class HealthVisualizer:
    """Generate visualizations for health metrics."""
    
    def create_health_report(
        self,
        session: Session,
        analysis: HealthAnalysis,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Create comprehensive health visualization.
        
        Args:
            session: Trace session
            analysis: Health analysis results
            output_dir: Directory to save plots (defaults to current dir)
        
        Returns:
            Path to saved visualization
        
        Raises:
            ImportError: If matplotlib not installed
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError(
                "matplotlib is required for visualizations. "
                "Install with: pip install mudipu[health]"
            )
        
        if output_dir is None:
            output_dir = Path.cwd()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from session ID
        session_id_short = str(session.session_id)[:8]
        output_path = output_dir / f"health_report_{session_id_short}.png"
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            f"Health Report: {session.name or 'Session ' + session_id_short}",
            fontsize=16,
            fontweight='bold'
        )
        
        # Plot 1: Context Growth
        self._plot_context_growth(axes[0, 0], session)
        
        # Plot 2: Health Trends
        self._plot_health_trends(axes[0, 1], analysis.per_turn)
        
        # Plot 3: Component Breakdown
        self._plot_component_breakdown(axes[1, 0], analysis.per_turn)
        
        # Plot 4: Session Summary
        self._plot_session_summary(axes[1, 1], analysis.session)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return output_path
    
    def _plot_context_growth(self, ax, session: Session):
        """Plot prompt token growth over turns."""
        turns = [t.turn_number for t in session.turns]
        tokens = [
            t.usage.get("prompt_tokens", 0) if t.usage else 0
            for t in session.turns
        ]
        
        ax.plot(turns, tokens, marker='o', linewidth=2, markersize=6, color='#2E86AB')
        ax.set_xlabel("Turn Number", fontsize=10)
        ax.set_ylabel("Prompt Tokens", fontsize=10)
        ax.set_title("Context Growth", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Annotate with tool calls
        for i, turn in enumerate(session.turns):
            if turn.tool_calls_detected:
                tool_names = [
                    tc.function_name for tc in turn.tool_calls_detected
                    if tc.function_name
                ]
                if tool_names:
                    label = ", ".join(tool_names[:2])  # Max 2 tools
                    if len(tool_names) > 2:
                        label += "..."
                    ax.annotate(
                        label,
                        (turns[i], tokens[i]),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha='center',
                        fontsize=7,
                        alpha=0.7,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3)
                    )
    
    def _plot_health_trends(self, ax, turn_metrics: List[TurnHealthMetrics]):
        """Plot health score trends over turns."""
        turns = [m.turn_number for m in turn_metrics]
        health = [m.health_score for m in turn_metrics]
        relevance = [m.relevance_score for m in turn_metrics]
        novelty = [m.novelty_score for m in turn_metrics]
        
        ax.plot(turns, health, marker='o', label='Overall Health', linewidth=2, color='#06A77D')
        ax.plot(turns, relevance, marker='s', label='Relevance', alpha=0.7, color='#F77E21')
        ax.plot(turns, novelty, marker='^', label='Novelty', alpha=0.7, color='#D883B7')
        
        # Threshold line
        ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Threshold', linewidth=1)
        
        ax.set_xlabel("Turn Number", fontsize=10)
        ax.set_ylabel("Score", fontsize=10)
        ax.set_title("Health Trends", fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_ylim([0, 1.1])
    
    def _plot_component_breakdown(self, ax, turn_metrics: List[TurnHealthMetrics]):
        """Plot metric components over turns."""
        turns = [m.turn_number for m in turn_metrics]
        
        metrics = {
            'Relevance': [m.relevance_score for m in turn_metrics],
            'Anti-Duplicate': [1 - m.duplicate_ratio for m in turn_metrics],
            'Anti-Saturation': [1 - m.saturation_score for m in turn_metrics],
            'Anti-Loop': [1 - m.tool_loop_score for m in turn_metrics],
            'Novelty': [m.novelty_score for m in turn_metrics],
        }
        
        colors = ['#2E86AB', '#A23B72', '#F77E21', '#06A77D', '#D883B7']
        
        # Plot each metric
        for (label, values), color in zip(metrics.items(), colors):
            ax.plot(turns, values, marker='o', label=label, alpha=0.7, markersize=4, color=color)
        
        ax.set_xlabel("Turn Number", fontsize=10)
        ax.set_ylabel("Score", fontsize=10)
        ax.set_title("Component Breakdown", fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_ylim([0, 1.1])
    
    def _plot_session_summary(self, ax, session_metrics: SessionHealthMetrics):
        """Plot session-level summary as bar chart."""
        metrics = {
            'Overall\nHealth': session_metrics.overall_health,
            'Progress': session_metrics.progress_score,
            'Effectiveness': session_metrics.effectiveness_score,
            'Anti-Drift': 1 - session_metrics.drift_score,
            'Anti-Loop': 1 - session_metrics.loop_score,
        }
        
        labels = list(metrics.keys())
        values = list(metrics.values())
        
        # Color based on score
        colors = []
        for v in values:
            if v >= 0.7:
                colors.append('#06A77D')  # Green
            elif v >= 0.5:
                colors.append('#F77E21')  # Orange
            else:
                colors.append('#D32F2F')  # Red
        
        bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Threshold line
        ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=0.7, color='green', linestyle='--', alpha=0.3, linewidth=1)
        
        ax.set_ylabel("Score", fontsize=10)
        ax.set_title("Session Summary", fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1.1])
        ax.tick_params(axis='x', labelsize=8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 0.02,
                f'{height:.2f}',
                ha='center',
                va='bottom',
                fontsize=9,
                fontweight='bold'
            )
        
        # Add legend for color coding
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#06A77D', label='Healthy (≥0.7)'),
            Patch(facecolor='#F77E21', label='Moderate (0.5-0.7)'),
            Patch(facecolor='#D32F2F', label='Unhealthy (<0.5)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=7)
    
    def plot_token_growth_simple(
        self,
        session: Session,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Create a simple token growth chart.
        
        Args:
            session: Trace session
            output_path: Where to save (if None, displays instead)
        
        Returns:
            Path if saved, None if displayed
        """
        try:
            import matplotlib
            if output_path:
                matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError(
                "matplotlib is required. Install with: pip install mudipu[health]"
            )
        
        turns = [t.turn_number for t in session.turns]
        tokens = [
            t.usage.get("prompt_tokens", 0) if t.usage else 0
            for t in session.turns
        ]
        
        plt.figure(figsize=(10, 6))
        plt.plot(turns, tokens, marker='o', linewidth=2, markersize=8)
        plt.xlabel("Turn Number")
        plt.ylabel("Prompt Tokens")
        plt.title(f"Context Growth: {session.name or 'Session'}")
        plt.grid(True, alpha=0.3)
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None
