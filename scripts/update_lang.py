import json
from pathlib import Path
import os

def main():
    config_path = Path.home() / 'agi/configs/rhythm_prefs.json'
    print(f"Updating {config_path}...")
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error reading config: {e}")
            config = {}
    else:
        print("Config file not found, creating new.")
        config = {}
        
    config['system_language'] = 'ko'
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Successfully updated system_language to 'ko'")
    except Exception as e:
        print(f"❌ Failed to write config: {e}")

if __name__ == "__main__":
    main()
