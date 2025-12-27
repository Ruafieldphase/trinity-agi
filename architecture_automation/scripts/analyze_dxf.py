import ezdxf
import sys
import os

def analyze_dxf(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        print(f"📂 Evaluating: {os.path.basename(file_path)}")
        print(f"   DXF Version: {doc.dxfversion}")
        
        layers = {}
        total_entities = 0
        
        for e in msp:
            total_entities += 1
            layer = e.dxf.layer
            dxftype = e.dxftype()
            
            if layer not in layers:
                layers[layer] = {"count": 0, "types": {}}
            
            layers[layer]["count"] += 1
            if dxftype not in layers[layer]["types"]:
                layers[layer]["types"][dxftype] = 0
            layers[layer]["types"][dxftype] += 1
            
        print(f"   Total Entities: {total_entities}")
        print("-" * 40)
        print(f"{'Layer Name':<20} | {'Count':<6} | {'Entity Types'}")
        print("-" * 40)
        
        for layer_name, data in sorted(layers.items()):
            types_str = ", ".join([f"{k}:{v}" for k,v in data["types"].items()])
            print(f"{layer_name:<20} | {data['count']:<6} | {types_str}")
            
    except Exception as e:
        print(f"❌ Error reading DXF: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_dxf(sys.argv[1])
    else:
        print("Usage: python analyze_dxf.py <path_to_dxf>")
