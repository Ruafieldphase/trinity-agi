import time
import sys
import os
import shutil
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
PROJECT_ROOT = WORKSPACE_ROOT / "architecture_automation"
INPUT_DIR = PROJECT_ROOT / "inputs"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_DIR = WORKSPACE_ROOT / "logs"
PARSER_SCRIPT = PROJECT_ROOT / "scripts" / "dxf_parser_engine.py"

# Logging Setup
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "blueprint_watcher.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BlueprintWatcher")

class BlueprintHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filename = Path(event.src_path).name
        if filename.lower().endswith(".dxf"):
            logger.info(f"📐 New Blueprint detected: {filename}")
            self.process_dxf(Path(event.src_path))

    def process_dxf(self, dxf_path):
        """Call the parser engine to process the DXF"""
        # Wait a moment for file copy to complete
        time.sleep(1)
        
        try:
            logger.info(f"⚙️  Processing {dxf_path.name}...")
            
            # Trigger Parser Engine
            cmd = [sys.executable, str(PARSER_SCRIPT), str(dxf_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                logger.info(f"✅ Parsing Complete: {result.stdout.strip()}")
            else:
                logger.error(f"❌ Parsing Failed: {result.stderr}")
            
        except Exception as e:
            logger.error(f"❌ Error processing {dxf_path.name}: {e}")

def start_watcher():
    if not INPUT_DIR.exists():
        INPUT_DIR.mkdir(parents=True)
        logger.info(f"📂 Created input directory: {INPUT_DIR}")
    
    event_handler = BlueprintHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INPUT_DIR), recursive=False)
    observer.start()
    
    logger.info(f"👀 Watching for Blueprints in: {INPUT_DIR}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watcher()
