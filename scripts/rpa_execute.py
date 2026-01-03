#!/usr/bin/env python3
"""
RPA Execute CLI - Direct tutorial execution
Phase 2.5 Week 3 Day 14

Usage:
    python scripts/rpa_execute.py --text "1. Open notepad 2. Type hello"
    python scripts/rpa_execute.py --file tutorial.txt --mode LIVE
    python scripts/rpa_execute.py --text "..." --verify --failsafe
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List
from workspace_root import get_workspace_root

# Ensure imports work
ROOT = get_workspace_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fdo_agi_repo.rpa.execution_engine import ExecutionEngine, ExecutionConfig, ExecutionMode, ExecutionResult


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments"""
    p = argparse.ArgumentParser(
        description="RPA Execute CLI - Run tutorial automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run simulation
  python scripts/rpa_execute.py --text "1. Open notepad\\n2. Type hello world"
  
  # Live execution with verification
  python scripts/rpa_execute.py --file tutorial.txt --mode LIVE --verify
  
  # Verify existing screenshots
  python scripts/rpa_execute.py --file tutorial.txt --mode VERIFY_ONLY
  
  # Full safety mode
  python scripts/rpa_execute.py --text "..." --mode LIVE --verify --failsafe --confirm
        """
    )
    
    # Input
    input_group = p.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", type=str, help="Tutorial text directly")
    input_group.add_argument("--file", type=Path, help="Tutorial text file")
    
    # Execution mode
    p.add_argument(
        "--mode", 
        type=str, 
        default="DRY_RUN",
        choices=["DRY_RUN", "LIVE", "VERIFY_ONLY"],
        help="Execution mode (default: DRY_RUN)"
    )
    
    # Features
    p.add_argument("--verify", action="store_true", help="Enable verification")
    p.add_argument("--no-screenshots", action="store_true", help="Disable screenshots")
    p.add_argument("--no-failsafe", action="store_true", help="Disable failsafe")
    p.add_argument("--confirm", action="store_true", help="Require confirmation before LIVE execution")
    
    # Verifier settings
    p.add_argument("--similarity", type=float, default=0.95, help="Similarity threshold (0-1, default: 0.95)")
    p.add_argument("--comparison", type=str, default="SSIM", choices=["SSIM", "MSE"], help="Comparison method")
    
    # Failsafe settings
    p.add_argument("--timeout", type=float, default=30.0, help="Timeout seconds (default: 30)")
    p.add_argument("--retries", type=int, default=3, help="Max retries (default: 3)")
    
    # Output
    p.add_argument("--output", type=Path, help="Output JSON file for result")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    return p.parse_args(argv)


def load_tutorial_text(args: argparse.Namespace) -> str:
    """Load tutorial text from args"""
    if args.text:
        return args.text
    elif args.file:
        if not args.file.exists():
            raise FileNotFoundError(f"Tutorial file not found: {args.file}")
        return args.file.read_text(encoding="utf-8")
    else:
        raise ValueError("Either --text or --file must be provided")


def confirm_live_execution(tutorial_text: str) -> bool:
    """Prompt user to confirm live execution"""
    print("\n" + "="*60)
    print("⚠️  LIVE EXECUTION MODE")
    print("="*60)
    print("\nThis will perform REAL actions on your computer:")
    print(tutorial_text[:200] + ("..." if len(tutorial_text) > 200 else ""))
    print("\n" + "="*60)
    
    response = input("\nProceed with live execution? (yes/no): ").strip().lower()
    return response in ("yes", "y")


def print_result(result: ExecutionResult, args: argparse.Namespace):
    """Print execution result"""
    print("\n" + "="*60)
    print("🎯 EXECUTION RESULT")
    print("="*60)
    print(f"Success: {'✅' if result.success else '❌'} {result.success}")
    print(f"Mode: {result.mode.value}")
    print(f"Tutorial: {result.tutorial_name}")
    print(f"Total Actions: {result.total_actions}")
    print(f"Executed: {result.executed_actions}")
    print(f"Verified: {result.verified_actions}")
    print(f"Failed: {result.failed_actions}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    
    if result.errors:
        print(f"\n❌ Errors ({len(result.errors)}):")
        for i, err in enumerate(result.errors[:5], 1):
            print(f"  {i}. {err}")
    
    print("="*60 + "\n")
    
    # Save to file if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        print(f"📄 Result saved to: {args.output}")


def main(argv: Optional[List[str]] = None):
    """Main entry point"""
    args = parse_args(argv)
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logger = logging.getLogger("rpa_execute")
    
    try:
        # Load tutorial
        tutorial_text = load_tutorial_text(args)
        logger.info(f"Loaded tutorial: {len(tutorial_text)} characters")
        
        # Confirm if needed
        mode = ExecutionMode[args.mode]
        if mode == ExecutionMode.LIVE and args.confirm:
            if not confirm_live_execution(tutorial_text):
                logger.info("Execution cancelled by user")
                return 0
        
        # Build config
        config = ExecutionConfig(
            mode=mode,
            enable_verification=args.verify,
            enable_screenshots=not args.no_screenshots,
            enable_failsafe=not args.no_failsafe,
            confirmation_required=args.confirm,
            similarity_threshold=args.similarity,
            comparison_method=args.comparison,
            timeout=args.timeout,
            max_retries=args.retries,
        )
        
        logger.info(f"Execution config: mode={config.mode.value}, verify={config.enable_verification}, failsafe={config.enable_failsafe}")
        
        # Execute
        engine = ExecutionEngine(config)
        result = engine.execute_tutorial(tutorial_text)
        
        # Print result
        print_result(result, args)
        
        return 0 if result.success else 1
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
