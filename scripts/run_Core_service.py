#!/usr/bin/env python3
import asyncio
import logging
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Add workspace root to path
WORKSPACE_ROOT = get_workspace_root()
sys.path.append(str(WORKSPACE_ROOT))

# Import CoreAdapter
# Note: CoreAdapter expects fdo_agi_repo to be in path or accessible
# It is under WORKSPACE_ROOT/fdo_agi_repo
# But the import in CoreAdapter is `from ...orchestrator.core_system import CoreSystem`
# which implies it expects to be imported as part of a package or with correct path setup.
# Let's adjust sys.path to ensure imports work.

# We need to make sure 'fdo_agi_repo' is importable if we import it fully qualified
# OR if we import from within.
# CoreAdapter is in fdo_agi_repo.structure.adapters.core_adapter

try:
    from fdo_agi_repo.structure.adapters.core_adapter import CoreAdapter
except ImportError:
    # Fallback if fdo_agi_repo is not a package
    sys.path.append(str(WORKSPACE_ROOT / "fdo_agi_repo"))
    from structure.adapters.core_adapter import CoreAdapter

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(WORKSPACE_ROOT / "outputs" / "core_service.log")
    ]
)
logger = logging.getLogger("CoreService")

async def main():
    logger.info("Starting Core Service...")
    logger.info(f"Workspace Root: {WORKSPACE_ROOT}")
    
    try:
        adapter = CoreAdapter(workspace_root=str(WORKSPACE_ROOT))
        await adapter.initialize()
        
        logger.info("Core Adapter initialized. Starting loop...")
        
        while True:
            try:
                await adapter.rhythm()
                # logger.info("Tick")
                await asyncio.sleep(5) # 5 seconds interval
            except Exception as e:
                logger.error(f"Error in Core loop: {e}")
                await asyncio.sleep(5)
                
    except Exception as e:
        logger.critical(f"Fatal error initializing Core Service: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
