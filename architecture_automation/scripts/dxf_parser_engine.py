import ezdxf
import json
import sys
import os
from pathlib import Path

# Configuration
# Add typical layer names found in Korean architectural drawings
WALL_LAYERS = [
    "WALL", "벽체", "CONC", "CONCRETE", "옹벽", "조적", "C-WALL",
    "A-WALL", "WALL-1", "WALL-2", "골조", "마감", 
    "경량철골", "석고보드", "단열재", "외곽",
    "0", "Defpoints"
]
WINDOW_LAYERS = ["WINDOW", "창호", "GLASS", "유리", "DOOR", "문", "DOORS"]
ELEVATION_LAYERS = ["ELE", "입면", "FRONT", "RIGHT", "LEFT", "BACK", "배면", "좌측", "우측", "정면"]

import math

def calculate_centroid(entities):
    """Calculate the geometric center of a list of entities"""
    if not entities:
        return (0, 0)
    
    sum_x, sum_y = 0, 0
    count = 0
    
    for e in entities:
        if e['type'] == 'line':
            sum_x += (e['start'][0] + e['end'][0]) / 2
            sum_y += (e['start'][1] + e['end'][1]) / 2
            count += 1
        elif e['type'] == 'polyline':
            # Simple average of points
            px = sum(p[0] for p in e['points']) / len(e['points'])
            py = sum(p[1] for p in e['points']) / len(e['points'])
            sum_x += px
            sum_y += py
            count += 1
            
    if count == 0: return (0, 0)
    return (sum_x / count, sum_y / count)

def cluster_entities(entities, distance_threshold=5000):
    """Group entities into clusters based on proximity"""
    clusters = []
    
    # Simple recursive clustering (Graph-based connected components)
    # Note: For huge DXFs, this O(N^2) might be slow. Optimization: Grid hashing.
    # For now, we use a simplified bounding box approach or just filtering outliers.
    
    # 1. Calculate bounding box for all entities
    # If standard floor plan, entities are dense.
    # We will pick the "Largest Cluster" by entity count.
    
    return [entities] # Placeholder: Return all as one cluster for now if logic is complex
    # Enhancing logic below

def extract_geometry(dxf_path):
    print(f"📖 Reading: {dxf_path}...")
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
    except Exception as e:
        print(f"❌ Failed to read DXF: {e}")
        return None

    all_entities = []
    
    extracted_data = {
        "walls": [],
        "elevations": [],
        "windows": [],
        "doors": []
    }

    print("   Scanning entities (exploding blocks)...")
    
    # helper to process a primitive
    def process_primitive(e, category):
        try:
            if e.dxftype() == 'LINE':
                return {
                    "category": category,
                    "type": "line",
                    "start": [e.dxf.start.x, e.dxf.start.y],
                    "end": [e.dxf.end.x, e.dxf.end.y]
                }
            elif e.dxftype() == 'LWPOLYLINE':
                points = []
                # virtual entities lwpolyline usually has points iterator
                with e.points() as p_iter:
                    for p in p_iter:
                         points.append([p[0], p[1]])
                return {
                    "category": category,
                    "type": "polyline",
                    "points": points,
                    "closed": e.closed
                }
        except:
            return None
        return None

    # Iterate over all entities in modelspace, decomposing blocks
    # query() allows filtering by layer first to save time? 
    # But layer properties might be on definitions.
    # We iterate all top level, if it matches layer -> keep.
    # If it is INSERT, we must check if its sub-entities are on the target layer?
    # Or usually, the INSERT itself is on "WALL" layer?
    # Let's try iterating ALL modelspace and extracting virtual entities.
    
    count_scanned = 0
    
    for entity in msp:
        count_scanned += 1
        
        # Check Layer of the TOP entity first
        layer_name = entity.dxf.layer.upper()
        
        # Simple Filter: If Top Entity is on target layer -> Explode and keep all parts
        # OR If Top Entity is INSERT, we might need to look inside.
        # Strategy: Let's explode everything that is potentially relevant.
        
        entity_category = None
        if any(name in layer_name for name in WALL_LAYERS):
            entity_category = "walls"
        elif any(name in layer_name for name in ELEVATION_LAYERS):
            entity_category = "elevations"
        elif any(name in layer_name for name in WINDOW_LAYERS):
            entity_category = "windows"
        
        # If the container itself (Block Ref) is on the layer, we take all its geometry
        if entity_category:
            try:
                # virtual_entities() creates a generator of primitives
                for primitive in entity.virtual_entities():
                    data = process_primitive(primitive, entity_category)
                    if data:
                        # FILTER: Ignore small objects (details, screws)
                        length = 0
                        if data['type'] == 'line':
                            dx = data['end'][0] - data['start'][0]
                            dy = data['end'][1] - data['start'][1]
                            length = (dx**2 + dy**2)**0.5
                        elif data['type'] == 'polyline':
                            # Rough length (bounding box diagonal? or contour?)
                            # Let's verify perimeter or bbox diagonal
                            # Simplified: Check if points span large area
                            xs = [p[0] for p in data['points']]
                            ys = [p[1] for p in data['points']]
                            if xs and ys:
                                dx = max(xs) - min(xs)
                                dy = max(ys) - min(ys)
                                length = (dx**2 + dy**2)**0.5
                                
                        if length > 500: # 500mm Threshold
                             all_entities.append(data)
            except Exception as e:
                pass
            continue
            
        # Strategy 2: If the Block Ref is on Layer '0', but inside data is on 'WALL'?
        # That requires deep inspection. For now, assume architecture practice:
        # Walls are drawn on Wall layer.
        # But if we missed it before, maybe we should be more aggressive.
        # Let's iterate EVERYTHING if it is an INSERT.
        
        if entity.dxftype() == 'INSERT':
            try:
                 for primitive in entity.virtual_entities():
                     # Check layer of the PRIMITIVE (inside the block)
                     p_layer = primitive.dxf.layer.upper()
                     p_cat = None
                     if any(name in p_layer for name in WALL_LAYERS):
                         p_cat = "walls"
                     elif any(name in p_layer for name in ELEVATION_LAYERS):
                         p_cat = "elevations"
                     elif any(name in p_layer for name in WINDOW_LAYERS):
                         p_cat = "windows"
                     
                     if p_cat:
                         data = process_primitive(primitive, p_cat)
                         if data:
                            # FILTER: Ignore small objects
                            length = 0
                            if data['type'] == 'line':
                                dx = data['end'][0] - data['start'][0]
                                dy = data['end'][1] - data['start'][1]
                                length = (dx**2 + dy**2)**0.5
                            elif data['type'] == 'polyline':
                                xs = [p[0] for p in data['points']]
                                ys = [p[1] for p in data['points']]
                                if xs and ys:
                                    dx = max(xs) - min(xs)
                                    dy = max(ys) - min(ys)
                                    length = (dx**2 + dy**2)**0.5
                                    
                            if length > 500:
                                 all_entities.append(data)
            except:
                pass

    print(f"   Found {len(all_entities)} candidate entities.")
    
    # CLUSTERING LOGIC (Simple Grid Hashing)
    # We group entities that are close to each other.
    # Grid size = 10000 units (Assuming mm, 10 meters)
    grid = {}
    GRID_SIZE = 5000 
    
    for e in all_entities:
        # Use centroid for hashing
        pk = (0,0)
        if e['type'] == 'line':
            pk = ((e['start'][0] + e['end'][0])/2, (e['start'][1] + e['end'][1])/2)
        else:
            pk = (e['points'][0][0], e['points'][0][1])
            
        grid_key = (int(pk[0] // GRID_SIZE), int(pk[1] // GRID_SIZE))
        if grid_key not in grid:
            grid[grid_key] = []
        grid[grid_key].append(e)
        
    print(f"   Spatial Grid: {len(grid)} cells occupied.")
    
    # Find the "densest" area (Cluster of 3x3 grids)
    # This assumes the main building is the densest part of the drawing
    max_count = 0
    best_center = None
    
    cluster_scores = {}
    
    for gx, gy in grid.keys():
        # Check 3x3 neighbors
        score = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                neighbor = (gx + dx, gy + dy)
                if neighbor in grid:
                    score += len(grid[neighbor])
        
        cluster_scores[(gx, gy)] = score
        if score > max_count:
            max_count = score
            best_center = (gx, gy)
            
    if not best_center:
        print("❌ No geometry found.")
        return None
        
    print(f"   Detected Main Cluster at Grid {best_center} with score {max_count}")
    
    # Collect entities from the main cluster (3x3 area)
    final_entities = []
    cx, cy = best_center
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
             neighbor = (cx + dx, cy + dy)
             if neighbor in grid:
                 final_entities.extend(grid[neighbor])
                 
    # Categorize back
    for e in final_entities:
        cat = e.pop('category')
        extracted_data[cat].append(e)

    print(f"✅ Extracted Architectural Elements")
    print(f"   - Walls: {len(extracted_data['walls'])}")
    print(f"   - Elevations: {len(extracted_data['elevations'])}")
    print(f"   - Windows: {len(extracted_data['windows'])}")
    
    return extracted_data

def save_json(data, original_path):
    output_path = Path(original_path).parent.parent / "outputs" / "parsed_blueprint.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved JSON to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dxf_file = sys.argv[1]
        data = extract_geometry(dxf_file)
        if data:
            save_json(data, dxf_file)
    else:
        print("Usage: python dxf_parser_engine.py <dxf_file_path>")
