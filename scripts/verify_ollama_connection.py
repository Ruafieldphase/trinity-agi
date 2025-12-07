import argparse
import requests
import sys

def verify_ollama(ip, port=11434):
    url = f"http://{ip}:{port}/api/tags"
    print(f"📡 Connecting to Ollama at {url}...")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Connection Successful!")
            print(f"🧠 Available Models ({len(models)}):")
            for m in models:
                print(f"  - {m['name']}")
            return True
        else:
            print(f"❌ Connection Failed: Status {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Failed: Could not connect to {ip}:{port}")
        print("   (Check if Ollama is running and firewall allows port 11434)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Remote Ollama Connection")
    parser.add_argument("ip", help="IP address of the Linux node running Ollama")
    args = parser.parse_args()
    
    success = verify_ollama(args.ip)
    sys.exit(0 if success else 1)
