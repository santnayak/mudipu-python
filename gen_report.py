from mudipu.exporters.html_exporter import HTMLExporter
from mudipu.models import Session, BaseTurn, ToolCall
from pathlib import Path

s = Session(name="Gateway Demo", tags=["demo", "openrouter", "tools"])

t1 = BaseTurn(
    turn_number=1,
    model="openai/gpt-4o-mini",
    duration_ms=812.3,
    request_messages=[
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": "What is the weather in London and Paris right now?"}
    ],
    response_message={"role": "assistant", "content": None},
    tool_calls_detected=[
        ToolCall(function_name="get_weather", function_arguments='{"city": "London"}'),
        ToolCall(function_name="get_weather", function_arguments='{"city": "Paris"}'),
    ],
    has_tool_calls=True,
    usage={"prompt_tokens": 142, "completion_tokens": 38, "total_tokens": 180},
)
s.add_turn(t1)

t2 = BaseTurn(
    turn_number=2,
    model="openai/gpt-4o-mini",
    duration_ms=1241.7,
    request_messages=[
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": "What is the weather in London and Paris right now?"},
        {"role": "tool", "content": "London: 14\u00b0C, Overcast. Humidity 78%. Wind 12 km/h SW."},
        {"role": "tool", "content": "Paris: 18\u00b0C, Partly cloudy. Humidity 62%. Wind 8 km/h NW."},
    ],
    response_message={
        "role": "assistant",
        "content": "Here is the current weather:\n\n**London**: 14\u00b0C, overcast with 78% humidity and a 12 km/h south-westerly breeze.\n\n**Paris**: 18\u00b0C, partly cloudy with 62% humidity and a lighter 8 km/h north-westerly wind.\n\nParis is warmer and less humid right now if you are deciding between the two!"
    },
    has_tool_calls=False,
    usage={"prompt_tokens": 284, "completion_tokens": 91, "total_tokens": 375},
)
s.add_turn(t2)

t3 = BaseTurn(
    turn_number=3,
    model="openai/gpt-4o-mini",
    duration_ms=654.1,
    request_messages=[
        {"role": "user", "content": "Which city would you recommend for a weekend trip?"},
    ],
    response_message={
        "role": "assistant",
        "content": "Based on the weather, I would recommend **Paris** for a weekend trip. The milder temperature of 18\u00b0C and partly cloudy skies make it ideal for outdoor sightseeing \u2014 strolling along the Seine, visiting the Louvre, or sitting at a caf\u00e9 in Montmartre. London at 14\u00b0C with overcast skies is still pleasant but might require an extra layer!"
    },
    has_tool_calls=False,
    usage={"prompt_tokens": 471, "completion_tokens": 78, "total_tokens": 549},
)
s.add_turn(t3)
s.end_session()

health_metrics = {
    "per_turn": [
        {"turn_number": 1, "relevance_score": 0.91, "duplicate_ratio": 0.05, "saturation_score": 0.12, "tool_loop_score": 0.08, "novelty_score": 0.88, "health_score": 0.87, "details": {}},
        {"turn_number": 2, "relevance_score": 0.85, "duplicate_ratio": 0.18, "saturation_score": 0.21, "tool_loop_score": 0.04, "novelty_score": 0.76, "health_score": 0.79, "details": {}},
        {"turn_number": 3, "relevance_score": 0.78, "duplicate_ratio": 0.22, "saturation_score": 0.34, "tool_loop_score": 0.03, "novelty_score": 0.61, "health_score": 0.71, "details": {}},
    ],
    "session": {
        "session_id": str(s.session_id),
        "turns_analyzed": 3,
        "context_growth_rate": 92.3,
        "drift_score": 0.11,
        "loop_score": 0.06,
        "progress_score": 0.82,
        "effectiveness_score": 0.79,
        "overall_health": 0.79,
        "details": {"has_loops": False},
    }
}

out = Path("C:/DEV_PERSONAL/mudipu-github/mudipu-python/sample_report.html")
ex = HTMLExporter(output_dir=out.parent)
ex.export(s, filename=out.name, health_metrics=health_metrics)
print("Written to:", out)
