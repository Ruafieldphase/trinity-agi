#!/usr/bin/env python3
"""
Generate Autonomous Dashboard with Orchestration
Phase 5.5: Monitoring + Orchestration Unified View

통합 대시보드:
  - 채널 건강도
  - 라우팅 권장사항
  - 복구 상태
  - 실시간 메트릭
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from workspace_root import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()


def run_command(cmd: list[str]) -> tuple[int, str]:
    """Run command and return (exit_code, output)"""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.returncode, result.stdout + result.stderr


def generate_dashboard(open_browser: bool = True) -> int:
    """
    Generate autonomous monitoring dashboard with orchestration
    
    Args:
        open_browser: Open in browser after generation
    
    Returns:
        Exit code (0=success)
    """
    print("🎯 Generating Autonomous Dashboard...")
    print("=" * 60)
    
    # Step 1: Generate monitoring metrics
    print("\n[1/3] Generating monitoring metrics...")
    code, _ = run_command([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(WORKSPACE_ROOT / "scripts" / "generate_monitoring_report.ps1"),
        "-Hours", "24"
    ])
    if code != 0:
        print("❌ Failed to generate monitoring metrics")
        return 1
    print("✅ Monitoring metrics generated")
    
    # Step 2: Generate orchestration section (HTML fragment)
    print("\n[2/3] Generating orchestration section...")
    code, orch_html = run_command([
        sys.executable,
        str(WORKSPACE_ROOT / "scripts" / "generate_orchestration_section.py")
    ])
    if code != 0:
        print(f"❌ Failed to generate orchestration section")
        return 1
    print("✅ Orchestration section generated")
    
    # Step 3: Build final HTML (inject into placeholder if present)
    print("\n[3/3] Building final dashboard...")
    dashboard_path = WORKSPACE_ROOT / "outputs" / "autonomous_dashboard_latest.html"
    
    # Read base dashboard
    base_dashboard_path = WORKSPACE_ROOT / "outputs" / "monitoring_dashboard_latest.html"
    if not base_dashboard_path.exists():
        print(f"❌ Base dashboard not found: {base_dashboard_path}")
        return 1
    
    base_html = base_dashboard_path.read_text(encoding="utf-8")
    
    # Try to inject into placeholder first (Phase 5.5+ template)
    placeholder = '<div class="container mt-5" id="orchestration-section-placeholder">'
    if placeholder in base_html:
        print("  → Injecting into orchestration-section-placeholder")
        final_html = base_html.replace(
            placeholder,
            f'{placeholder}\n{orch_html}'
        )
    else:
        # Fallback: Insert before </body> (legacy behavior)
        print("  → Placeholder not found, appending before </body>")
        insertion_point = base_html.rfind("</body>")
        if insertion_point == -1:
            print("❌ Could not find </body> tag")
            return 1
        
        final_html = (
            base_html[:insertion_point] +
            f'\n    <div class="container mt-5">\n{orch_html}\n    </div>\n' +
            base_html[insertion_point:]
        )
    
    # Add title update
    final_html = final_html.replace(
        "<title>Monitoring Dashboard</title>",
        "<title>Autonomous Monitoring Dashboard (with Orchestration)</title>"
    )
    
    dashboard_path.write_text(final_html, encoding="utf-8")
    print(f"✅ Dashboard saved: {dashboard_path}")
    
    # Optional: Open in browser
    if open_browser:
        print("\n📖 Opening dashboard in browser...")
        subprocess.run(["start", str(dashboard_path)], shell=True)
    
    print("\n" + "=" * 60)
    print("✅ Autonomous Dashboard Generated Successfully!")
    print(f"📂 Location: {dashboard_path}")
    return 0


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Autonomous Dashboard")
    parser.add_argument("--no-open", dest="open_browser", action="store_false", help="Don't open browser")
    parser.add_argument("--open", dest="open_browser", action="store_true", help="Open in browser (default)")
    parser.set_defaults(open_browser=True)
    
    args = parser.parse_args()
    
    try:
        exit_code = generate_dashboard(open_browser=args.open_browser)
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
