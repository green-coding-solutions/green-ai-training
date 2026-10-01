import ollama

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

def get_weather(city):
    if city == 'Berlin':
        return 'Berlin is always nice and sunny 14° C'
    elif city == 'Potsdam':
        return 'Potsdam stinks, so the weather is irrelevant!'
    else:
        return f"I do not have any data for {city}. Try a different one!"

response = ollama.chat(
    model="qwen2.5-coder:7b",
    messages=[
        {
            "role": "user",
            "content": "What's the weather in Berlin?"
        }
    ],
    tools=tools
)

print(response)