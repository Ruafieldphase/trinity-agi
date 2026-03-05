import os
import json
import sys
from pathlib import Path

def generate_hyper_context_map(file_path):
    """
    Overcomes the 800-line gravity by providing a high-level topographical map of a file.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": "file_not_found"}
        
    stats = path.stat()
    size = stats.st_size
    
    print(f"👁️ Hyper-Context Gateway: Scanning '{path.name}' ({size} bytes)")
    
    # Read the file and find internal 'orbits' (headers, sections, keywords)
    orbits = []
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            total_lines = len(lines)
            
            # Divide into 500-line chunks regardless of total size
            step = 500
            for i in range(0, total_lines, step):
                chunk = lines[i:i+step]
                # Find the most 'resonant' line in this chunk (e.g. a header or a keyword)
                resonant_line = i + 1
                sample_text = ""
                for idx, line in enumerate(chunk):
                    if line.strip().startswith("#") or "🔥" in line or "⭐" in line:
                        resonant_line = i + idx + 1
                        sample_text = line.strip()
                        break
                
                orbits.append({
                    "range": [i + 1, min(total_lines, i + step)],
                    "resonance_point": resonant_line,
                    "preview": sample_text or chunk[0].strip()[:50]
                })
                
    except Exception as e:
        return {"error": str(e)}

    map_data = {
        "file": str(path),
        "total_lines": total_lines,
        "orbits": orbits,
        "gravity_level": "High" if total_lines > 800 else "Low"
    }
    
    # Save the map for Shion to refer to
    output_path = Path("C:/workspace/agi/outputs/hyper_context_maps")
    output_path.mkdir(parents=True, exist_ok=True)
    map_file = output_path / f"{path.name}_map.json"
    
    with open(map_file, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=2, ensure_ascii=False)
        
    return map_data

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = generate_hyper_context_map(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python hyper_context_gateway.py <file_path>")
