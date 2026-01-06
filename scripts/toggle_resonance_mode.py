import os
import json
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "configs")
CONFIG_PATH = os.path.join(CONFIG_DIR, "resonance_config.json")
EXAMPLE_PATH = os.path.join(CONFIG_DIR, "resonance_config.example.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        if os.path.exists(EXAMPLE_PATH):
            print("Creating config from example...")
            with open(EXAMPLE_PATH, 'r', encoding='utf-8') as src, open(CONFIG_PATH, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        else:
            print("Creating minimal config...")
            os.makedirs(CONFIG_DIR, exist_ok=True)
            default_config = {
                "active_mode": "observe",
                "default_policy": "quality-first",
                "policies": {
                    "quality-first": {"min_quality": 0.8, "require_evidence": True, "max_latency_ms": 8000}
                }
            }
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Toggle Resonance Mode")
    parser.add_argument("--mode", choices=['disabled', 'observe', 'enforce'], default='observe')
    parser.add_argument("--policy", help="Policy name")
    args = parser.parse_args()

    config = load_config()
    prev_mode = config.get("active_mode", "unknown")
    
    config["active_mode"] = args.mode
    
    if args.policy:
        if "policies" in config and args.policy in config["policies"]:
            config["active_policy"] = args.policy
        else:
            print(f"Warning: Policy '{args.policy}' not found. Keeping existing policy.")

    save_config(config)
    
    print("Resonance configuration updated:")
    print(f"  {prev_mode} -> {args.mode}")
    print(f"  Path: {CONFIG_PATH}")
    if args.policy:
        print(f"  Active policy: {config.get('active_policy', 'unchanged')}")

if __name__ == "__main__":
    main()
