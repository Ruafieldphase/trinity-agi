#!/usr/bin/env python3
"""
VS Code settings.json Validator
Checks JSON syntax and reports statistics
Used by system_health_check.ps1
"""
import json
import sys
from pathlib import Path

def main():
    settings_path = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    
    if not settings_path.exists():
        print(f"ERROR|File not found: {settings_path}")
        sys.exit(1)
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Count terminal history entries
        history_count = 0
        issues = []
        
        if 'terminal.integrated.shellIntegration.commandHistory' in data:
            history_count = len(data['terminal.integrated.shellIntegration.commandHistory'])
            
            # Check for PowerShell check_monitoring_status.ps1 duplicates
            history = data['terminal.integrated.shellIntegration.commandHistory']
            ps_monitoring_cmds = [
                k for k in history.keys() 
                if 'powershell' in k.lower() and 'check_monitoring_status.ps1' in k
            ]
            
            if len(ps_monitoring_cmds) > 1:
                issues.append(f"{len(ps_monitoring_cmds)} duplicate PowerShell monitoring commands")
        
        if issues:
            print(f"WARNING|{history_count} commands, issues: {'; '.join(issues)}")
            sys.exit(0)
        else:
            print(f"OK|{history_count}")
            sys.exit(0)
            
    except json.JSONDecodeError as e:
        print(f"ERROR|JSON parse error at line {e.lineno}: {e.msg}")
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"ERROR|Encoding error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"ERROR|{str(e)}")
        sys.exit(3)

if __name__ == '__main__':
    main()
