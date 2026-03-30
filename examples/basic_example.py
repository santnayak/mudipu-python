"""
Basic example of using Mudipu SDK with OpenAI.
"""

from mudipu import MudipuTracer, trace_llm
from openai import OpenAI


def main():
    """Main example function."""
    # Initialize tracer
    tracer = MudipuTracer(session_name="basic-example", tags=["example", "openai"])

    # Create OpenAI client
    client = OpenAI()

    # Start tracing session
    with tracer.trace_session():
        # Define a traced LLM function
        @trace_llm(model="gpt-4")
        def ask_question(question: str) -> str:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": question},
                ],
            )
            return response.choices[0].message.content

        # Make some LLM calls
        answer1 = ask_question("What is the capital of France?")
        print(f"Answer 1: {answer1}")

        answer2 = ask_question("What is 2 + 2?")
        print(f"Answer 2: {answer2}")

        answer3 = ask_question("Tell me a short joke.")
        print(f"Answer 3: {answer3}")

    print("\n✓ Session completed! Check .mudipu/traces/ for exported traces.")


if __name__ == "__main__":
    main()
