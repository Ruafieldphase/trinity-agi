from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class MaterialProperties:
    label: str
    thickness: float  # Standard thickness in mm (Constant C derivative)
    color_hint: str   # RGB or hex hint for visualization
    density: float    # kg/m3 for potential future mass calcs

class MaterialLibrary:
    """
    Provides architectural material constants to the ARI engine.
    Maps visual/textual labels to structural metadata.
    """
    def __init__(self):
        self.materials: Dict[str, MaterialProperties] = {
            "rc_wall": MaterialProperties("Reinforced Concrete Wall", 200.0, "#808080", 2400.0),
            "brick_wall": MaterialProperties("Brick Wall", 100.0, "#A52A2A", 1800.0),
            "glass_partition": MaterialProperties("Glass Partition", 12.0, "#ADD8E6", 2500.0),
            "wood_floor": MaterialProperties("Wood Flooring", 15.0, "#8B4513", 700.0),
            "drywall": MaterialProperties("Drywall/Gypsum", 12.5, "#F5F5F5", 800.0),
            "insulation": MaterialProperties("Thermal Insulation", 50.0, "#FFFACD", 30.0),
        }

    def get_material(self, label: str) -> Optional[MaterialProperties]:
        # Simple fuzzy or exact match
        clean_label = label.lower().replace(" ", "_").replace("-", "_")
        for key, props in self.materials.items():
            if key in clean_label or clean_label in key:
                return props
        return None

    def list_materials(self) -> Dict[str, MaterialProperties]:
        return self.materials

if __name__ == "__main__":
    lib = MaterialLibrary()
    wall = lib.get_material("RC-Wall")
    if wall:
        print(f"Found: {wall.label}, Thickness: {wall.thickness}mm")
