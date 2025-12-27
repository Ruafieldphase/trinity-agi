import json
import os
import time
from pathlib import Path

def get_dir_state(path: Path):
    if not path.exists():
        return {"exists": False}
    try:
        st = path.stat()
        return {
            "exists": True,
            "mtime": st.st_mtime,
            "size": st.st_size if path.is_file() else 0,
            "is_dir": path.is_dir()
        }
    except Exception:
        return {"exists": True, "error": "access_denied"}

def main():
    root = Path(__file__).resolve().parents[1]
    
    # Network-free monitoring targets
    targets = [
        root / "outputs",
        root / "memory",
        root / "outputs" / "bridge"
    ]
    
    metrics = {
        "scan_time": time.time(),
        "targets": {}
    }
    
    for t in targets:
        metrics["targets"][t.name] = get_dir_state(t)
        # 1-depth sub-scan for outputs
        if t.name == "outputs" and t.exists():
            metrics["targets"]["outputs_files"] = {}
            for child in t.glob("*"):
                metrics["targets"]["outputs_files"][child.name] = get_dir_state(child)

    out = root / "outputs" / "monitoring_metrics_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write (write then replace)
    temp = out.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        os.replace(temp, out)
    except Exception:
        pass
    
    print(json.dumps({"ok": True, "out": str(out)}))

if __name__ == "__main__":
    main()
