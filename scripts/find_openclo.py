import os

search_term = "오픈클로"
root_dir = r"C:\workspace\agi"

for root, dirs, files in os.walk(root_dir):
    if "node_modules" in dirs:
        dirs.remove("node_modules")
    if ".git" in dirs:
        dirs.remove(".git")
    for file in files:
        if file.endswith((".py", ".md", ".txt", ".json", ".bat", ".ps1")):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if search_term in content:
                        print(f"Found in: {file_path}")
            except:
                pass
