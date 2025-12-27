import bpy
import json
import os
import sys

# Argument Parsing (Blender Python ignores standard sys.argv)
# Usage: blender --background --python blender_connector.py -- <json_file> <output_blend>
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

if len(argv) < 2:
    print("Usage: blender -P blender_connector.py -- <json_file> <output_blend>")
    # Don't exit here if run inside Blender UI for testing
else:
    JSON_PATH = argv[0]
    OUTPUT_BLEND = argv[1]

    # --- BLENDER AUTOMATION LOGIC ---

    def clean_scene():
        """Delete everything in the scene"""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

    def create_wall(start, end, height=2.4):
        """Create a wall from start to end points"""
        # Calculate length and rotation
        x1, y1 = start
        x2, y2 = end
        
        dx = x2 - x1
        dy = y2 - y1
        length = (dx**2 + dy**2)**0.5
        angle = 0
        
        import math
        angle = math.atan2(dy, dx)
        
        # Determine center
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        
        # Create Cube (Wall)
        thickness = 0.2  # 200mm wall thickness assumption
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, height/2))
        obj = bpy.context.active_object
        obj.name = "Wall"
        
        # Scale
        obj.scale = (length, thickness, height)
        
        # Rotate
        obj.rotation_euler[2] = angle

    def process_blueprint(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        walls = data.get("walls", [])
        print(f"🔨 Processing {len(walls)} entities into Curves...")

        # 1. Calculate Bounding Box Center
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        has_data = False
        for w in walls:
            points = []
            if w['type'] == 'line':
                points = [w['start'], w['end']]
            elif w['type'] == 'polyline':
                points = w['points']
            
            for p in points:
                has_data = True
                min_x = min(min_x, p[0])
                min_y = min(min_y, p[1])
                max_x = max(max_x, p[0])
                max_y = max(max_y, p[1])
                
        center_x, center_y = 0, 0
        if has_data:
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            print(f"📍 Recentering geometry from ({center_x}, {center_y}) to Origin")

        # Create Collection
        if "Blueprint" not in bpy.data.collections:
            collection = bpy.data.collections.new("Blueprint")
            bpy.context.scene.collection.children.link(collection)
        else:
            collection = bpy.data.collections["Blueprint"]
            
        layer = bpy.context.view_layer
        active_layer_collection = layer.layer_collection.children['Blueprint']
        layer.active_layer_collection = active_layer_collection

        # --- NEW CURVE LOGIC ---
        # Instead of making 3000 objects, we make ONE Curve object with 3000 splines.
        
        curve_data = bpy.data.curves.new('WallCurve', type='CURVE')
        curve_data.dimensions = '2D'
        curve_data.resolution_u = 2
        
        # Set Extrude Height directly on the curve (Walls)
        # Assuming units are meters. 2.4m height.
        # Note: Extrude in Blender Curves is "Half Height" in both directions if not offset?
        # Actually standard Extrude goes up along Z if 2D. 
        # Wait, Curve extrude adds depth. 
        curve_data.extrude = 2.4 / 2  # It extrudes symmetrically? Let's check. 
        # Usually easier to use Modifiers for precise control.
        # Let's use a Solidify Modifier approach or Geometry Nodes later?
        # User said: "Just make faces and connect".
        # Simplest Arch method: Curve -> Extrude property.
        
        # But for "Meji" (Joints), user said "Thickness".
        # So we might want TWO curves: "Walls" (Extrude) and "Details" (Bevel).
        # For now, put everything in one Wall Curve with simple extrusion.
        
        curve_object = bpy.data.objects.new('Imported_Walls', curve_data)
        collection.objects.link(curve_object)
        
        # Add Splines
        for w in walls:
            points = []
            if w['type'] == 'line':
                points = [w['start'], w['end']]
            elif w['type'] == 'polyline':
                points = w['points']
            
            if not points: continue
            
            # Recenter and Scale
            vectors = []
            for p in points:
                px = (p[0] - center_x) / 1000.0
                py = (p[1] - center_y) / 1000.0
                vectors.append((px, py, 0, 1)) # x,y,z,w (w not used for poly)
            
            # Create Poly Spline
            spline = curve_data.splines.new('POLY')
            spline.points.add(len(vectors) - 1) # One point exists by default
            
            for i, vec in enumerate(vectors):
                spline.points[i].co = vec
                
            if w.get('closed', False):
                spline.use_cyclic_u = True

        # Finish Setup - Wall Curve
        
        # Apply Solidify Modifier for Thickness (instead of Extrude)
        # 2D Curve + Extrude gives height. Solidify gives thickness.
        curve_data.extrude = 1.2 # Height (2.4m total)
        
        mod = curve_object.modifiers.new("WallThickness", 'SOLIDIFY')
        mod.thickness = 0.2 # 200mm Thickness
        mod.offset = 0 # Center alignment
        
        print("✅ Created Walls with Thickness.")

        # --- ELEVATION LOGIC ---
        elevations = data.get("elevations", [])
        if elevations:
            print(f"📐 Processing {len(elevations)} elevation lines...")
            ele_curve_data = bpy.data.curves.new('ElevationCurve', type='CURVE')
            ele_curve_data.dimensions = '2D'
            ele_object = bpy.data.objects.new('Imported_Elevations', ele_curve_data)
            collection.objects.link(ele_object)
            
            # Rotate 90 degrees on X to stand it up
            ele_object.rotation_euler[0] = 1.5708 # 90 deg in radians
            # Move slightly back so it doesn't intersect walls
            ele_object.location[1] = 10 # 10m back
            
            for w in elevations:
                points = []
                if w['type'] == 'line':
                    points = [w['start'], w['end']]
                elif w['type'] == 'polyline':
                    points = w['points']
                
                if not points: continue
                
                # Recenter (using same center as walls to match)
                vectors = []
                for p in points:
                    px = (p[0] - center_x) / 1000.0
                    py = (p[1] - center_y) / 1000.0
                    vectors.append((px, py, 0, 1))
                
                spline = ele_curve_data.splines.new('POLY')
                spline.points.add(len(vectors) - 1)
                for i, vec in enumerate(vectors):
                    spline.points[i].co = vec

            print("✅ Created Standing Elevation Reference.")

    # --- MAIN EXECUTION ---
    clean_scene()
    process_blueprint(JSON_PATH)
    
    # Save
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"✅ Saved Blender file: {OUTPUT_BLEND}")
