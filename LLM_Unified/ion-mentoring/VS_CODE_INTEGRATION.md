# VS Code Integration Helpers

This repository includes lightweight helpers to generate VS Code tasks and a simple status watcher.

Files:
- `vscode_integration.py`: Generates `.vscode/tasks.json` and `.vscode/commands.json` with curated tasks for common operations (monitoring, deploy, tests, load tests).
- `extension_api.py`: Provides a CLI to sync assets and a terminal-friendly status watcher that prints updates from a JSON state file.

Quick start (optional commands):

```powershell
# Generate .vscode/tasks.json and .vscode/commands.json at the workspace root
python .\LLM_Unified\ion-mentoring\vscode_integration.py --workspace-dir .

# Or use the unified helper
python .\LLM_Unified\ion-mentoring\extension_api.py sync --workspace-dir .

# Watch a JSON status file (update the path to your orchestrator state file)
python .\LLM_Unified\ion-mentoring\extension_api.py watch-status --state-file .\LLM_Unified\ion-mentoring\outputs\orchestrator_state.json --interval 1.0
```

Notes:
- The generated `commands.json` is for internal tooling or future extension work; VS Code does not consume it natively.
- You can re-run the sync at any time; generation is idempotent.
- To integrate live status, have your orchestrator write a JSON state file periodically and run the `watch-status` command as a background VS Code task.
