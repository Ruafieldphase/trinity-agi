import os
import math
import hashlib
from collections import Counter
from datetime import datetime

class RIOOrchestrator:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.md_files = []
        self.fields = {
            "unified_field": ["unified", "field", "resonance", "scalar"],
            "lumen": ["lumen", "session", "restore", "vscode"],
            "sovereign": ["sovereign", "api", "extraction", "livelihood"],
            "agi_core": ["agi", "consciousness", "thought", "unconscious"]
        }

    def scan_files(self):
        print(f"[*] Scanning for markdown files in {self.root_dir}...")
        for root, _, files in os.walk(self.root_dir):
            if any(x in root for x in ["node_modules", ".git", "venv", ".venv", "backups"]):
                continue
            for file in files:
                if file.endswith(".md"):
                    self.md_files.append(os.path.join(root, file))
        print(f"[+] Found {len(self.md_files)} files.")

    def calculate_entropy(self, text):
        if not text:
            return 0
        counter = Counter(text)
        length = len(text)
        entropy = 0
        for count in counter.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    def analyze_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            size = os.path.getsize(file_path)
            entropy = self.calculate_entropy(content)
            mtime = os.path.getmtime(file_path)
            
            # Determine Field
            assigned_field = "uncategorized"
            lower_content = content.lower()
            lower_path = file_path.lower()
            max_hits = 0
            for field, keywords in self.fields.items():
                hits = sum(1 for kw in keywords if kw in lower_content or kw in lower_path)
                if hits > max_hits:
                    max_hits = hits
                    assigned_field = field
            
            # --- HFA Layer Logic ---
            now = datetime.now().timestamp()
            days_since_mod = (now - mtime) / (24 * 3600)
            
            # 1. Pulse (Active Cortex): 7일 이내 수정된 활성 작업
            if days_since_mod < 7:
                layer = "pulse"
            
            # 2. Labyrinth (Heritage of Trials): 실패, 에러, 실험, 시도
            elif any(kw in lower_content for kw in ["error", "fail", "failed", "traceback", "exception", "broken", "debug", "test", "trial", "experiment"]):
                layer = "labyrinth"
            
            # 3. Monolith (Stable Systems): 성공, 완성, 릴리즈, 안정
            elif any(kw in lower_content for kw in ["success", "stable", "manifest", "release", "final", "core", "axiom"]) or size > 5000:
                layer = "monolith"
                
            # 4. Void (Archival): 그 외 오래되고 변화 없는 것들
            else:
                layer = "void"

            return {
                "path": file_path,
                "field": assigned_field,
                "layer": layer,
                "entropy": entropy,
                "size": size
            }
        except Exception as e:
            return None

    def orchestrate(self, dry_run=True):
        self.scan_files()
        results = []
        for f in self.md_files:
            analysis = self.analyze_file(f)
            if analysis:
                results.append(analysis)
        
        self.generate_report(results)
        
        print("\n[!] Orchestration Proposal generated at RIO_proposal.md")
        
        if not dry_run:
            self.execute_moves(results)

    def generate_report(self, results):
        report_path = "RIO_proposal.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# RIO: Information Orchestration Report\n\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total files analyzed: {len(results)}\n\n")
            
            # Summary Table
            f.write("## Overview\n\n")
            f.write("| Field | Pulse | Labyrinth | Monolith | Void | Total |\n")
            f.write("|---|---|---|---|---|---|\n")
            
            summary = {}
            for res in results:
                fld, lyr = res['field'], res['layer']
                if fld not in summary: summary[fld] = {"pulse": 0, "labyrinth": 0, "monolith": 0, "void": 0}
                summary[fld][lyr] += 1
            
            for fld, counts in summary.items():
                total = sum(counts.values())
                f.write(f"| {fld} | {counts['pulse']} | {counts['labyrinth']} | {counts['monolith']} | {counts['void']} | {total} |\n")
            
            # Details
            f.write("\n## Implementation Details\n\n")
            for fld in sorted(summary.keys()):
                f.write(f"### Field: {fld}\n\n")
                field_res = [r for r in results if r['field'] == fld]
                for lyr in ["pulse", "labyrinth", "monolith", "void"]:
                    lyr_res = [r for r in field_res if r['layer'] == lyr]
                    if lyr_res:
                        f.write(f"#### Layer: {lyr.upper()} ({len(lyr_res)} files)\n")
                        for r in lyr_res[:10]: # Limit to 10 per layer
                            f.write(f"- {os.path.basename(r['path'])} (`E:{r['entropy']:.2f}`)\n")
                        if len(lyr_res) > 10:
                            f.write(f"- ... and {len(lyr_res)-10} more\n")
                        f.write("\n")

    def execute_moves(self, results):
        import shutil
        print(f"\n[!] Executing moves for {len(results)} files...")
        
        for res in results:
            src = res['path']
            # Target path: field/layer/filename.md
            # Note: We group them into 'fields' or top-level?
            # User suggested /atlas, /pulse, /labyrinth, /monolith, /void
            # So the Field is a sub-folder within those?
            # Let's follow: layer/field/filename.md
            
            target_dir = os.path.join(self.root_dir, res['layer'], res['field'])
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            
            dest = os.path.join(target_dir, os.path.basename(src))
            
            if src == dest:
                continue
                
            try:
                # Handle filename collisions
                if os.path.exists(dest):
                    base, ext = os.path.splitext(dest)
                    dest = f"{base}_{hashlib.md5(src.encode()).hexdigest()[:4]}{ext}"
                
                shutil.move(src, dest)
            except Exception as e:
                print(f"[E] Failed to move {src} -> {dest}: {e}")
        
        print("[+] Orchestration complete.")

if __name__ == "__main__":
    orchestrator = RIOOrchestrator("c:\\workspace\\agi")
    orchestrator.orchestrate(dry_run=False)
