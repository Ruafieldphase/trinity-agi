import os
from pathlib import Path

from dotenv import load_dotenv
import google.generativeai as genai


def _load_env() -> None:
    root = Path(__file__).resolve().parent
    cred = root / ".env_credentials"
    if cred.exists():
        load_dotenv(dotenv_path=cred, override=False)
    load_dotenv(dotenv_path=root / ".env", override=False)


def main() -> int:
    _load_env()

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY/GEMINI_API_KEY not found.")
        return 2

    try:
        genai.configure(api_key=api_key)
        working_models: list[str] = []
        for m in genai.list_models():
            try:
                if "generateContent" not in getattr(m, "supported_generation_methods", []):
                    continue
                working_models.append(str(getattr(m, "name", "") or ""))
            except Exception:
                continue

        if not working_models:
            print("WARNING: No models found with 'generateContent'.")
            return 1

        preferred = "models/gemini-2.5-flash"
        test_model = preferred if preferred in working_models else working_models[0]
        model = genai.GenerativeModel(test_model)
        response = model.generate_content("Hello")
        ok = bool(response and getattr(response, "text", None))
        print(f"Model test: {test_model} -> {'OK' if ok else 'NO_TEXT'}")
        return 0 if ok else 1
    except Exception as e:
        print(f"ERROR: Script failed: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
