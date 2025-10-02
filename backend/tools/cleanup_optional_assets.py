"""Utility to prune legacy/optional assets from the streamlined codebase.

Usage examples (dry-run by default):

    python tools/cleanup_optional_assets.py
    python tools/cleanup_optional_assets.py --include-optional
    python tools/cleanup_optional_assets.py --include-optional --include-backups --execute

By default the script only targets files/directories linked to the deprecated
advanced AI pipeline. Additional categories can be opted-in via flags.
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CleanupTarget:
    relative_path: Path
    reason: str
    category: str

    @property
    def absolute_path(self) -> Path:
        return (PROJECT_ROOT / self.relative_path).resolve()

    @property
    def kind(self) -> str:
        path = self.absolute_path
        if path.exists():
            return "dir" if path.is_dir() else "file"
        # Fallback to suffix to give users a hint in dry-run output
        return "dir" if self.relative_path.suffix == "" else "file"


ADVANCED_AI_TARGETS: List[CleanupTarget] = [
    CleanupTarget(Path("demo_advanced_ai.py"), "Legacy demo for removed transformer pipeline.", "advanced-ai"),
    CleanupTarget(Path("setup_advanced_ai.py"), "Setup helper for deprecated advanced AI stack.", "advanced-ai"),
    CleanupTarget(Path("setup_ollama.py"), "Ollama bootstrap script no longer required.", "advanced-ai"),
    CleanupTarget(Path("train_legal_bert.py"), "Training script for removed Legal BERT models.", "advanced-ai"),
    CleanupTarget(Path("app/ml/inference/legacy_compliance_engine.py"), "Torch-based legacy engine superseded by simple pipeline.", "advanced-ai"),
    CleanupTarget(Path("app/ml/inference/legacy_rule_classifier.py"), "Unused rule classifier heuristics.", "advanced-ai"),
    CleanupTarget(Path("models/enhanced_compliance"), "Large artifacts for the deprecated enhanced model.", "advanced-ai"),
    CleanupTarget(Path("models/legal_bert_compliance"), "Legal BERT classifier artifacts no longer used.", "advanced-ai"),
    CleanupTarget(Path("models/legal_bert_rule_classification"), "Rule classification checkpoints for removed pipeline.", "advanced-ai"),
]

OPTIONAL_TARGETS: List[CleanupTarget] = [
    CleanupTarget(Path("api/legacy_main.py"), "Legacy FastAPI entrypoint kept for migration reference.", "optional"),
    CleanupTarget(Path("api/v1/endpoints/legacy_compliance.py"), "Unused router referencing compatibility wrapper.", "optional"),
    CleanupTarget(Path("demo_system.py"), "Old CLI demo using compatibility wrapper.", "optional"),
    CleanupTarget(Path("updated_compliance_system.py"), "Compatibility layer superseded by new service flow.", "optional"),
    CleanupTarget(Path("models/rule_based_compliance"), "Legacy rule-based pipeline artifacts.", "optional"),
    CleanupTarget(Path("models/simple_compliance_balanced"), "Alternative training snapshot no longer referenced.", "optional"),
]

BACKUP_TARGETS: List[CleanupTarget] = [
    CleanupTarget(Path("backup_pre_migration"), "Archived pre-migration sources and binaries.", "backup"),
]

LOG_TARGETS: List[CleanupTarget] = [
    CleanupTarget(Path("logs"), "Runtime log directory; safe to regenerate.", "logs"),
    CleanupTarget(Path("root_cleanup.log"), "Historical cleanup log from migration.", "logs"),
    CleanupTarget(Path("root_cleanup_log.json"), "Structured cleanup log from migration.", "logs"),
]


def gather_targets(args: argparse.Namespace) -> List[CleanupTarget]:
    targets: List[CleanupTarget] = list(ADVANCED_AI_TARGETS)

    if args.include_optional:
        targets.extend(OPTIONAL_TARGETS)
    if args.include_backups:
        targets.extend(BACKUP_TARGETS)
    if args.include_logs:
        targets.extend(LOG_TARGETS)

    # Remove duplicates while preserving order
    seen: set[Path] = set()
    deduped: List[CleanupTarget] = []
    for target in targets:
        rel = target.relative_path
        if rel in seen:
            continue
        seen.add(rel)
        deduped.append(target)
    return deduped


def validate_within_project(path: Path) -> None:
    try:
        path.relative_to(PROJECT_ROOT)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Refusing to touch path outside project root: {path}") from exc


def remove_path(path: Path) -> str:
    if not path.exists():
        return "missing"

    if path.is_dir():
        shutil.rmtree(path)
        return "deleted"

    path.unlink()
    return "deleted"


def format_status(status: str, kind: str, target: CleanupTarget) -> str:
    rel = target.relative_path.as_posix()
    return f"{status:<8} {kind:<4} {rel} — {target.reason}"


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Remove legacy/optional assets from the project.")
    parser.add_argument("--execute", action="store_true", help="Actually delete files instead of dry-run output.")
    parser.add_argument("--include-optional", action="store_true", help="Also remove migration leftovers and demos.")
    parser.add_argument("--include-backups", action="store_true", help="Also remove archived pre-migration sources.")
    parser.add_argument("--include-logs", action="store_true", help="Also purge generated log files/directories.")

    args = parser.parse_args(list(argv) if argv is not None else None)

    targets = gather_targets(args)
    if not targets:
        print("No targets selected. Nothing to do.")
        return

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"Cleanup mode: {mode}\nProject root: {PROJECT_ROOT}\n")

    for target in targets:
        path = target.absolute_path
        validate_within_project(path)
        kind = target.kind
        if args.execute:
            status = remove_path(path)
        else:
            status = "exists" if path.exists() else "missing"
        print(format_status(status, kind, target))

    if not args.execute:
        print("\nDry-run complete. Re-run with --execute to apply deletions.")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
