"""
Example using configuration file.
"""

from pathlib import Path
from mudipu import MudipuConfig, set_config, MudipuTracer, trace_llm
from openai import OpenAI


def main():
    """Example using custom configuration."""
    # Create custom configuration
    config = MudipuConfig(
        enabled=True,
        trace_dir=Path("./my_traces"),
        auto_export=True,
        export_format="both",  # Export both JSON and HTML
        redact_enabled=True,
        debug=True,
        verbose=True,
    )

    # Set as global config
    set_config(config)

    # Save config to file for future use
    config.to_yaml(Path("mudipu.yaml"))
    print("✓ Configuration saved to mudipu.yaml")

    # Now use the tracer with this config
    tracer = MudipuTracer(session_name="config-example", tags=["example", "custom-config"])

    client = OpenAI()

    with tracer.trace_session():

        @trace_llm(model="gpt-3.5-turbo")
        def ask_question(question: str) -> str:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": question}]
            )
            return response.choices[0].message.content

        answer = ask_question("What is machine learning?")
        print(f"\nAnswer: {answer}")

    print(f"\n✓ Session completed! Traces exported to {config.trace_dir}")
    print("  - JSON file for programmatic access")
    print("  - HTML file for visual inspection")


if __name__ == "__main__":
    main()
