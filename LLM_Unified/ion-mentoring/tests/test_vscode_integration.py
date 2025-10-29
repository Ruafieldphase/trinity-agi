import json
from pathlib import Path

from extension_api import run_status_loop, sync_vscode_assets
from vscode_integration import default_repo_tasks, generate_commands_json, write_tasks_json


def test_generate_tasks_and_commands(tmp_path: Path):
    vscode_dir = tmp_path / ".vscode"
    tasks = default_repo_tasks(workspace_folder_var="${workspaceFolder}")
    out_tasks = write_tasks_json(vscode_dir, tasks)
    out_cmds = generate_commands_json(vscode_dir, tasks)

    assert out_tasks.exists()
    data = json.loads(out_tasks.read_text(encoding="utf-8"))
    assert data.get("version") == "2.0.0"
    assert isinstance(data.get("tasks"), list) and len(data.get("tasks")) >= 10

    labels = [t["label"] for t in data["tasks"]]
    assert "Python: Run All Tests (repo venv)" in labels

    assert out_cmds.exists()
    cmds = json.loads(out_cmds.read_text(encoding="utf-8"))
    assert "commands" in cmds and len(cmds["commands"]) == len(tasks)


def test_sync_assets_and_status_watch(tmp_path: Path):
    # Sync assets
    sync_vscode_assets(tmp_path, ".vscode")
    assert (tmp_path / ".vscode" / "tasks.json").exists()
    assert (tmp_path / ".vscode" / "commands.json").exists()

    # Prepare a fake state file and watch it briefly
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"status": "ok", "ts": 1}), encoding="utf-8")
    rc = run_status_loop(state_file, interval_seconds=0.1, max_iterations=1)
    assert rc == 0
