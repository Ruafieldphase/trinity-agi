import os

search_term = "AGI-Aura"
root_dir = r"c:\workspace\agi"

print(f"Searching for '{search_term}' in {root_dir}...")

for dirpath, dirnames, filenames in os.walk(root_dir):
    # Skip .git, .venv, etc to speed up and avoid noise
    if ".git" in dirpath or ".venv" in dirpath or "__pycache__" in dirpath:
        continue
        
    for filename in filenames:
        if filename.lower().endswith(('.py', '.bat', '.ps1', '.vbs', '.cmd', '.json')):
            full_path = os.path.join(dirpath, filename)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if search_term in content:
                        print(f"FOUND in: {full_path}")
                        # Print context
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if search_term in line:
                                print(f"  Line {i+1}: {line.strip()}")
            except Exception as e:
                print(f"Could not read {full_path}: {e}")
