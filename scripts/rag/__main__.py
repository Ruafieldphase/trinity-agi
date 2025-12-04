from __future__ import annotations

import argparse
from importlib import import_module
import sys
from typing import Dict, Tuple, Optional

CommandInfo = Tuple[Optional[str], str]

COMMANDS: Dict[str, CommandInfo] = {
    "build": ("scripts.rag.build_index", "Build or merge an evidence index"),
    "describe": ("scripts.rag.describe_index", "Summarise index statistics"),
    "query": ("scripts.rag.query_cli", "Run retrieval queries against the index"),
    "quickstart": ("scripts.rag.quickstart", "Validate + describe + sample query"),
    "report": ("scripts.rag.report", "Generate Markdown/JSON index reports"),
    "validate": ("scripts.rag.validate_index", "Check index structure and embeddings"),
    "list": (None, "List available commands"),
}


def _print_command_list() -> None:
    print("Available commands:\n")
    for name in sorted(COMMANDS.keys()):
        module, description = COMMANDS[name]
        if module is None:
            print(f"  {name:<11} {description}")
        else:
            print(f"  {name:<11} {description} (module: {module})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAG tooling dispatcher. Example: python -m scripts.rag query --help"
    )
    parser.add_argument(
        "command",
        choices=sorted(COMMANDS.keys()),
        nargs="?",
        default="list",
        help="Subcommand to execute.",
    )
    args, remaining = parser.parse_known_args()

    module_name, _ = COMMANDS[args.command]
    if module_name is None:
        _print_command_list()
        return

    module = import_module(module_name)
    if hasattr(module, "main"):
        sys.argv = [module_name] + remaining
        module.main()
    else:
        raise SystemExit(f"Module {module_name} has no main()")


if __name__ == "__main__":
    main()
