import os
import google.generativeai as genai

def list_models():
    api_key = "AIzaSyAF5KquOJmisabOzX1O2xxiNLVI6qa1s88"
    genai.configure(api_key=api_key)
    try:
        models = genai.list_models()
        print("Available models:")
        for m in models:
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
