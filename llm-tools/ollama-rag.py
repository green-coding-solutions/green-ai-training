
import ollama
import argparse
import json
import re

from include import github_pr, green_search

DEFAULT_MODEL = "gemma4"

SYSTEM_PROMPT = (
    "You are a green coding assistant. When the user asks about the energy use, energy saving or efficiency "
    "of a coding technique, call search_green_measurements and base your answer only on the measured figures "
    "it returns. Quote the figures with their condition, mention that they come from Green Metrics Tool "
    "micro-benchmarks and add the measurement link. If no measurement fits, say so instead of guessing."
)

# Tools from the include directory: schema for the model, function to run
tools = [green_search.TOOL, github_pr.TOOL]

available_functions = {
    "search_green_measurements": green_search.search_green_measurements,
    "get_pull_request": github_pr.get_pull_request,
}

# Some models (e.g. qwen2.5-coder) do not return structured tool_calls but
# write the call as JSON into the content, optionally wrapped in ```json fences
# or <tool_call> tags. Parse those so the tool actually gets executed.
def parse_tool_calls_from_content(content):
    if not content:
        return []

    candidates = re.findall(r"<tool_call>(.*?)</tool_call>", content, re.DOTALL)
    candidates += re.findall(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
    if not candidates:
        candidates = [content]

    calls = []
    for candidate in candidates:
        try:
            data = json.loads(candidate.strip())
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("name") in available_functions:
                arguments = item.get("arguments", item.get("parameters", {}))
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                calls.append(ollama.Message.ToolCall(
                    function=ollama.Message.ToolCall.Function(name=item["name"], arguments=arguments)
                ))
    return calls


# Execute tool calls
def execute_tool(tool_call):
    name = tool_call.function.name
    arguments = tool_call.function.arguments

    print(f"\n[Tool call: {name}({arguments})]")

    if name not in available_functions:
        result = f"Error: Unknown tool '{name}'"
    else:
        try:
            result = str(available_functions[name](**arguments))
        except Exception as e:
            result = f"Tool execution error: {e}"

    print(f"[Tool result: {result}]\n")
    return result


parser = argparse.ArgumentParser(description="Chat with a local Ollama model that looks up measured green coding energy figures")
parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model to chat with (default: {DEFAULT_MODEL})")
args = parser.parse_args()
MODEL = args.model

# Conversation state
messages = [{"role": "system", "content": SYSTEM_PROMPT}]


# Main REPL loop
print(f"Chat started with {MODEL}")
print("Commands: /clear, /exit\n")

while True:
    user_input = input("You: ").strip()

    if not user_input:
        continue

    if user_input == "/exit":
        print("Goodbye!")
        break

    if user_input == "/clear":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("Conversation cleared.\n")
        continue

    # Add user message to conversation
    messages.append({
        "role": "user",
        "content": user_input
    })

    # LLM inference loop
    while True:
        stream = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=tools,
            stream=True
        )

        # Print tokens as they arrive and accumulate the full message
        content = ""
        streamed_tool_calls = []
        print("\nAssistant: ", end="", flush=True)
        for chunk in stream:
            if chunk.message.content:
                print(chunk.message.content, end="", flush=True)
                content += chunk.message.content
            if chunk.message.tool_calls:
                streamed_tool_calls.extend(chunk.message.tool_calls)
        print("\n")

        assistant_message = ollama.Message(
            role="assistant",
            content=content,
            tool_calls=streamed_tool_calls or None
        )

        tool_calls = assistant_message.tool_calls or parse_tool_calls_from_content(assistant_message.content)

        # Preserve the assistant message, including (possibly parsed) tool calls
        if tool_calls and not assistant_message.tool_calls:
            assistant_message.tool_calls = tool_calls
            assistant_message.content = ""
        messages.append(assistant_message)

        # Check whether the model requested a tool
        if not tool_calls:
            break

        # Execute all requested tools
        for tool_call in tool_calls:
            result = execute_tool(tool_call)

            # Append tool result to conversation
            messages.append({
                "role": "tool",
                "tool_name": tool_call.function.name,
                "content": result
            })

        # Loop continues: model is called again with tool results
