import google.generativeai as genai

def list_models():
    key = "AIzaSyCDhVwJAN1AZ8HLpyemSLy5KQtH9LgI1IQ"
    genai.configure(api_key=key)
    try:
        print("Listing models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    list_models()
