import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
sys.path.append(str(Path.cwd() / "services"))

try:
    from services.fsd_controller import FSDController
    print("✓ FSDController import successful")
    
    try:
        controller = FSDController(use_obs=False) # Skip OBS for quick test
        print("✓ FSDController instantiation successful")
    except Exception as e:
        print(f"❌ FSDController instantiation failed: {e}")

except Exception as e:
    print(f"❌ FSDController import failed: {e}")
    import traceback
    traceback.print_exc()
