import urllib.request
import sys

try:
    with urllib.request.urlopen("http://localhost:3000") as response:
        print(f"Status: {response.status}")
        print("Dashboard is accessible.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
