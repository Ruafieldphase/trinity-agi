import ezdxf
import sys
from collections import Counter

def inspect_layers(dxf_path):
    print(f"Inspecting layers in: {dxf_path}")
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
    except Exception as e:
        print(f"Error: {e}")
        return

    layers = Counter()
    for e in msp:
        layers[e.dxf.layer] += 1
    
    print("\nLayer Distribution (Top Level):")
    for layer, count in sorted(layers.items(), key=lambda x: x[1], reverse=True):
        print(f"{layer}: {count}")

    # Check common wall keywords in found layers
    print("\nPotential Architectural Layers (Filtered):")
    for layer in layers:
        l_upper = layer.upper()
        if any(kw in l_upper for kw in ["WALL", "벽체", "CON", "STL", " 골조", "STRUCTURE", "COLUMN", "기둥"]):
            print(f"MATCH: {layer} ({layers[layer]} entities)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_layers(sys.argv[1])
