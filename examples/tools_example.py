"""
Example showing tool call tracing.
"""

import time
from mudipu import MudipuTracer, trace_llm, trace_tool
from openai import OpenAI


@trace_tool("web_search")
def search_web(query: str) -> dict:
    """Simulate a web search tool."""
    # Simulate API delay
    time.sleep(0.2)

    # Return mock results
    return {
        "query": query,
        "results": [
            {"title": f"Result 1 for {query}", "url": "https://example.com/1"},
            {"title": f"Result 2 for {query}", "url": "https://example.com/2"},
        ],
    }


@trace_tool("database_query")
def query_database(sql: str) -> list:
    """Simulate a database query tool."""
    time.sleep(0.1)

    return [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ]


@trace_llm(model="gpt-4")
def call_llm_with_tools(messages: list[dict], tools: list[dict]) -> str:
    """Call LLM with tools available."""
    client = OpenAI()

    response = client.chat.completions.create(model="gpt-4", messages=messages, tools=tools)

    return response.choices[0].message.content


def main():
    """Main example showing tool usage."""
    tracer = MudipuTracer(session_name="tools-example", tags=["example", "tools"])

    with tracer.trace_session():
        # Define available tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "database_query",
                    "description": "Query the database",
                    "parameters": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]},
                },
            },
        ]

        # Simulate using tools
        print("Calling web search tool...")
        results = search_web("Python programming")
        print(f"Search results: {results}")

        print("\nQuerying database...")
        data = query_database("SELECT * FROM items")
        print(f"Database results: {data}")

        print("\nCalling LLM with tools...")
        response = call_llm_with_tools(
            messages=[{"role": "user", "content": "What can you help me with?"}], tools=tools
        )
        print(f"LLM response: {response}")

    print("\n✓ Session with tools completed! Check .mudipu/traces/ for exported traces.")


if __name__ == "__main__":
    main()
