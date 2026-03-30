"""
Tests for exporters.
"""


from mudipu.exporters.json_exporter import JSONExporter
from mudipu.exporters.html_exporter import HTMLExporter


def test_json_export(sample_session, temp_trace_dir):
    """Test JSON export."""
    exporter = JSONExporter(output_dir=temp_trace_dir)
    output_path = exporter.export(sample_session)

    assert output_path.exists()
    assert output_path.suffix == ".json"

    # Test loading
    loaded_session = exporter.load(output_path)
    assert loaded_session.session_id == sample_session.session_id
    assert loaded_session.turn_count == sample_session.turn_count


def test_html_export(sample_session, temp_trace_dir):
    """Test HTML export."""
    exporter = HTMLExporter(output_dir=temp_trace_dir)
    output_path = exporter.export(sample_session)

    assert output_path.exists()
    assert output_path.suffix == ".html"

    # Verify HTML contains key elements
    content = output_path.read_text()
    assert "Mudipu Trace" in content
    assert str(sample_session.session_id) in content
