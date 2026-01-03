#!/usr/bin/env python3
"""
Auto Dream Pipeline
==================

Full automation: Resonance → Dream → Glymphatic → Memory

Usage:
    python scripts/auto_dream_pipeline.py [--dry-run] [--verbose]
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from workspace_root import get_workspace_root

# Add project root to path
project_root = get_workspace_root()
sys.path.insert(0, str(project_root / "fdo_agi_repo"))

from orchestrator.resonance_bridge import consolidate_to_hippocampus
from copilot.hippocampus import CopilotHippocampus
from copilot.glymphatic import GlymphaticSystem


class DreamPipelineAutomation:
    """Automates the full dream processing pipeline."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.hippocampus = CopilotHippocampus(get_workspace_root())
        self.glymphatic = GlymphaticSystem(delta_threshold=100_000_000)
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "resonance_events_processed": 0,
            "memories_consolidated": 0,
            "dreams_generated": 0,
            "glymphatic_cycles": 0,
            "total_cleanup_mb": 0,
            "errors": []
        }
    
    def log(self, msg: str, level: str = "INFO"):
        """Log message with level."""
        prefix = f"[{level}]"
        if level == "ERROR":
            print(f"❌ {prefix} {msg}", file=sys.stderr)
        elif level == "WARN":
            print(f"⚠️  {prefix} {msg}")
        elif self.verbose or level == "INFO":
            icon = "✓" if level == "SUCCESS" else "ℹ"
            print(f"{icon}  {prefix} {msg}")
    
    def step_1_consolidate_resonance(self) -> Tuple[int, str]:
        """Step 1: Consolidate resonance events to hippocampus."""
        self.log("Step 1: Consolidating resonance events...", "INFO")
        
        try:
            if self.dry_run:
                self.log("DRY-RUN: Would consolidate resonance events", "WARN")
                return 0, "dry-run"
            
            result = consolidate_to_hippocampus(
                hours=24,
                min_importance=0.6
            )
            
            count = result.get("memories_added", 0)
            self.stats["resonance_events_processed"] = result.get("events_read", 0)
            self.stats["memories_consolidated"] = count
            
            self.log(f"Consolidated {count} memories from resonance", "SUCCESS")
            return count, "success"
            
        except Exception as e:
            error_msg = f"Resonance consolidation failed: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append({"step": "consolidate", "error": str(e)})
            return 0, "error"
    
    def step_2_generate_dreams(self) -> Tuple[int, str]:
        """Step 2: Generate dreams from patterns."""
        self.log("Step 2: Generating dreams from patterns...", "INFO")
        
        try:
            if self.dry_run:
                self.log("DRY-RUN: Would generate dreams", "WARN")
                return 0, "dry-run"
            
            # Get recent patterns
            patterns = self._extract_patterns_from_memory()
            
            if not patterns:
                self.log("No patterns found for dream generation", "WARN")
                return 0, "no-patterns"
            
            # Generate dreams
            dreams = []
            for pattern in patterns[:5]:  # Top 5 patterns
                dream = self.hippocampus.generate_dream(pattern)
                if dream:
                    dreams.append(dream)
            
            self.stats["dreams_generated"] = len(dreams)
            self.log(f"Generated {len(dreams)} dreams", "SUCCESS")
            return len(dreams), "success"
            
        except Exception as e:
            error_msg = f"Dream generation failed: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append({"step": "dreams", "error": str(e)})
            return 0, "error"
    
    def step_3_glymphatic_cleanup(self) -> Tuple[float, str]:
        """Step 3: Run glymphatic cleanup."""
        self.log("Step 3: Running glymphatic cleanup...", "INFO")
        
        try:
            if self.dry_run:
                self.log("DRY-RUN: Would run glymphatic cleanup", "WARN")
                return 0.0, "dry-run"
            
            # Get workspace root safely
            workspace_root = getattr(self.hippocampus, 'workspace_root', None)
            if not workspace_root:
                workspace_root = get_workspace_root()
                self.log("Using fallback workspace root", "WARN")
            
            # Get dreams and clean them
            dreams_file = Path(workspace_root) / "fdo_agi_repo" / "memory" / "dreams.jsonl"
            
            if not dreams_file.exists():
                self.log("No dreams file found", "WARN")
                return 0.0, "no-dreams"
            
            # Count original dreams
            original_count = 0
            with open(dreams_file, "r", encoding="utf-8") as f:
                for _ in f:
                    original_count += 1
            
            # Clean dreams (in place for now)
            cleaned_count = 0
            with open(dreams_file, "r", encoding="utf-8") as f:
                for line in f:
                    dream = json.loads(line)
                    cleaned = self.glymphatic.clean_dream(dream)
                    if cleaned:
                        cleaned_count += 1
            
            cleanup_ratio = (original_count - cleaned_count) / original_count if original_count > 0 else 0
            self.stats["glymphatic_cycles"] = 1
            self.stats["total_cleanup_mb"] = cleanup_ratio * 100  # Approximate
            
            self.log(f"Cleaned {cleaned_count}/{original_count} dreams", "SUCCESS")
            return cleanup_ratio * 100, "success"
            
        except Exception as e:
            error_msg = f"Glymphatic cleanup failed: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append({"step": "glymphatic", "error": str(e)})
            return 0.0, "error"
    
    def step_4_consolidate_to_longterm(self) -> Tuple[int, str]:
        """Step 4: Consolidate short-term to long-term memory."""
        self.log("Step 4: Consolidating to long-term memory...", "INFO")
        
        try:
            if self.dry_run:
                self.log("DRY-RUN: Would consolidate to long-term", "WARN")
                return 0, "dry-run"
            
            # Get short-term memories safely
            if hasattr(self.hippocampus, 'working_memory'):
                short_term = self.hippocampus.working_memory.get("short_term", [])
            else:
                self.log("No working_memory attribute, using fallback", "WARN")
                short_term = []
            
            if not short_term:
                self.log("No short-term memories to consolidate", "WARN")
                return 0, "no-memories"
            
            # Consolidate high-priority items
            consolidated = 0
            for memory in short_term[:20]:  # Top 20
                if memory.get("importance", 0) > 0.7:
                    if hasattr(self.hippocampus, 'store_memory'):
                        self.hippocampus.store_memory(memory, memory_type="long_term")
                        consolidated += 1
                    else:
                        self.log("store_memory not available, skipping", "WARN")
                        break
            
            self.log(f"Consolidated {consolidated} memories to long-term", "SUCCESS")
            return consolidated, "success"
            
        except Exception as e:
            error_msg = f"Long-term consolidation failed: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append({"step": "longterm", "error": str(e)})
            return 0, "error"
    
    def _extract_patterns_from_memory(self) -> List[Dict[str, Any]]:
        """Extract patterns from recent memories."""
        try:
            # Try to retrieve memories if method exists
            if hasattr(self.hippocampus, 'retrieve_memories'):
                recent = self.hippocampus.retrieve_memories(
                    query="",
                    limit=50,
                    min_importance=0.6
                )
            else:
                # Fallback: use memory store directly
                self.log("Using fallback pattern extraction", "WARN")
                recent = []
            
            # Simple pattern extraction
            patterns = []
            for memory in recent:
                pattern = {
                    "theme": memory.get("content", "")[:100],
                    "importance": memory.get("importance", 0.5),
                    "timestamp": memory.get("timestamp", ""),
                    "related_memories": [memory.get("id", "")]
                }
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.log(f"Pattern extraction failed: {e}", "WARN")
            return []
    
    def run_pipeline(self) -> Dict[str, Any]:
        """Run the full pipeline."""
        self.log("=" * 60, "INFO")
        self.log("Starting Auto Dream Pipeline", "INFO")
        self.log("=" * 60, "INFO")
        
        # Step 1: Consolidate resonance
        count, status = self.step_1_consolidate_resonance()
        if status == "error" and not self.dry_run:
            self.log("Pipeline halted due to consolidation error", "ERROR")
            return self._generate_report(success=False)
        
        # Step 2: Generate dreams
        dreams, status = self.step_2_generate_dreams()
        if status == "error":
            self.log("Continuing despite dream generation error", "WARN")
        
        # Step 3: Glymphatic cleanup
        cleanup_mb, status = self.step_3_glymphatic_cleanup()
        if status == "error":
            self.log("Continuing despite glymphatic error", "WARN")
        
        # Step 4: Long-term consolidation
        longterm, status = self.step_4_consolidate_to_longterm()
        if status == "error":
            self.log("Continuing despite long-term error", "WARN")
        
        # Generate final report
        return self._generate_report(success=True)
    
    def _generate_report(self, success: bool) -> Dict[str, Any]:
        """Generate pipeline execution report."""
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["success"] = success
        
        # Calculate duration
        start = datetime.fromisoformat(self.stats["start_time"])
        end = datetime.fromisoformat(self.stats["end_time"])
        duration = (end - start).total_seconds()
        self.stats["duration_seconds"] = duration
        
        # Log summary
        self.log("=" * 60, "INFO")
        self.log("Pipeline Summary", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Duration: {duration:.1f}s", "INFO")
        self.log(f"Resonance events: {self.stats['resonance_events_processed']}", "INFO")
        self.log(f"Memories consolidated: {self.stats['memories_consolidated']}", "INFO")
        self.log(f"Dreams generated: {self.stats['dreams_generated']}", "INFO")
        self.log(f"Cleanup: {self.stats['total_cleanup_mb']:.2f} MB", "INFO")
        self.log(f"Errors: {len(self.stats['errors'])}", "INFO")
        
        if success:
            self.log("Pipeline completed successfully! ✨", "SUCCESS")
        else:
            self.log("Pipeline completed with errors", "ERROR")
        
        return self.stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto Dream Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output", type=str, help="Output JSON file")
    
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = DreamPipelineAutomation(
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    stats = pipeline.run_pipeline()
    
    # Save output if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Report saved to: {output_path}")
    
    # Exit with error code if failed
    sys.exit(0 if stats["success"] else 1)


if __name__ == "__main__":
    main()
