"""
HTML exporter for trace data with interactive visualization.
"""
from pathlib import Path
from datetime import datetime
from typing import Optional
from jinja2 import Template

from mudipu.models import Session
from mudipu.config import get_config
from mudipu.version import __version__


class HTMLExporter:
    """
    Export trace sessions to HTML format with visualization.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize HTML exporter.
        
        Args:
            output_dir: Directory to write HTML files (defaults to config trace_dir)
        """
        config = get_config()
        self.output_dir = output_dir or config.trace_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, session: Session, filename: Optional[str] = None) -> Path:
        """
        Export a session to HTML file.
        
        Args:
            session: Session to export
            filename: Optional custom filename
            
        Returns:
            Path to the exported file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            session_name = session.name or "session"
            filename = f"{session_name}_{timestamp}_{session.session_id}.html"
        
        output_path = self.output_dir / filename
        
        # Render HTML
        html_content = self._render_html(session)
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return output_path
    
    def _render_html(self, session: Session) -> str:
        """Render session to HTML."""
        template = Template(HTML_TEMPLATE)
        
        return template.render(
            session=session,
            sdk_version=__version__,
            export_time=datetime.utcnow().isoformat(),
        )


# HTML Template with inline CSS and JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mudipu Trace: {{ session.name or session.session_id }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .metadata-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .metadata-label {
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metadata-value {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
            margin-top: 5px;
        }
        
        .turn {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .turn-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .turn-number {
            font-size: 1.2rem;
            font-weight: bold;
            color: #007bff;
        }
        
        .turn-meta {
            display: flex;
            gap: 15px;
            font-size: 0.9rem;
            color: #666;
        }
        
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid;
        }
        
        .message.user {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        
        .message.assistant {
            background: #f3e5f5;
            border-color: #9c27b0;
        }
        
        .message.system {
            background: #fff3e0;
            border-color: #ff9800;
        }
        
        .message-role {
            font-weight: bold;
            margin-bottom: 8px;
            text-transform: uppercase;
            font-size: 0.85rem;
        }
        
        .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .tool-calls {
            background: #fff8e1;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            border-left: 4px solid #ffc107;
        }
        
        .tool-call {
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }
        
        .tool-call-name {
            font-weight: bold;
            color: #f57c00;
        }
        
        .usage {
            display: flex;
            gap: 20px;
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.9rem;
        }
        
        .tag {
            display: inline-block;
            padding: 4px 12px;
            background: #007bff;
            color: white;
            border-radius: 12px;
            font-size: 0.85rem;
            margin: 0 5px;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 {{ session.name or 'Mudipu Trace Session' }}</h1>
            <div style="color: #666; margin-top: 10px;">
                Session ID: <code>{{ session.session_id }}</code>
                {% if session.tags %}
                <div style="margin-top: 10px;">
                    {% for tag in session.tags %}
                    <span class="tag">{{ tag }}</span>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            
            <div class="metadata">
                <div class="metadata-item">
                    <div class="metadata-label">Total Turns</div>
                    <div class="metadata-value">{{ session.turn_count }}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Total Duration</div>
                    <div class="metadata-value">{{ "%.2f"|format(session.total_duration_ms) }} ms</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Total Tokens</div>
                    <div class="metadata-value">{{ session.total_tokens }}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Created</div>
                    <div class="metadata-value">{{ session.created_at[:19] }}</div>
                </div>
            </div>
        </header>
        
        <main>
            {% for turn in session.turns %}
            <div class="turn">
                <div class="turn-header">
                    <span class="turn-number">Turn {{ turn.turn_number }}</span>
                    <div class="turn-meta">
                        {% if turn.model %}
                        <span>📦 {{ turn.model }}</span>
                        {% endif %}
                        {% if turn.duration_ms %}
                        <span>⏱️ {{ "%.2f"|format(turn.duration_ms) }} ms</span>
                        {% endif %}
                        <span>🕐 {{ turn.timestamp[:19] }}</span>
                    </div>
                </div>
                
                <!-- Request Messages -->
                {% for msg in turn.request_messages %}
                <div class="message {{ msg.role }}">
                    <div class="message-role">{{ msg.role }}</div>
                    <div class="message-content">{{ msg.content or msg.get('text', '') }}</div>
                </div>
                {% endfor %}
                
                <!-- Response Message -->
                {% if turn.response_message %}
                <div class="message assistant">
                    <div class="message-role">{{ turn.response_message.role or 'assistant' }}</div>
                    <div class="message-content">{{ turn.response_message.content or turn.response_message.get('text', '') }}</div>
                </div>
                {% endif %}
                
                <!-- Tool Calls -->
                {% if turn.tool_calls_detected %}
                <div class="tool-calls">
                    <strong>🔧 Tool Calls:</strong>
                    {% for tc in turn.tool_calls_detected %}
                    <div class="tool-call">
                        <span class="tool-call-name">{{ tc.function_name }}</span>
                        <div style="margin-top: 5px; font-size: 0.9rem;">
                            <code>{{ tc.function_arguments }}</code>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <!-- Usage Stats -->
                {% if turn.usage %}
                <div class="usage">
                    <span>📊 Prompt: {{ turn.usage.get('prompt_tokens', 0) }} tokens</span>
                    <span>Completion: {{ turn.usage.get('completion_tokens', 0) }} tokens</span>
                    <span>Total: {{ turn.usage.get('total_tokens', 0) }} tokens</span>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </main>
        
        <footer>
            Exported by Mudipu SDK v{{ sdk_version }} at {{ export_time[:19] }}
        </footer>
    </div>
</body>
</html>
"""
