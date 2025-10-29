"""
Simple test of Google Generative AI function calling
"""
import google.generativeai as genai
from google.generativeai import types

# Configure
genai.configure()

# Create a simple function
func = types.FunctionDeclaration(
    name="get_status",
    description="현재 상태를 확인합니다",
    parameters={
        "type": "object",
        "properties": {
            "detail_level": {
                "type": "string",
                "description": "상세도 (간단 또는 상세)"
            }
        }
    }
)

tool = types.Tool(function_declarations=[func])

print("✅ Tool created successfully")
print(f"Function name: {func.name}")
print(f"Tool has {len(tool.function_declarations)} functions")

# Try creating a model with the tool
model = genai.GenerativeModel(
    "gemini-2.0-flash-exp",
    tools=[tool]
)

print("✅ Model created successfully")
