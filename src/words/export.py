import zipfile
from datetime import datetime, timezone
from pathlib import Path

from words.paths import user_vocabulary_dir

_OVERLAY_FILENAMES = ("additions.csv", "removals.csv")


def default_export_filename(*, when: datetime | None = None) -> str:
    stamp = (when or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    return f"vipa-vocabulary-{stamp}.zip"


def collect_overlay_files(user_root: Path | None = None) -> list[Path]:
    root = user_vocabulary_dir() if user_root is None else user_root
    if not root.is_dir():
        return []

    files: list[Path] = []
    for language_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for filename in _OVERLAY_FILENAMES:
            candidate = language_dir / filename
            if candidate.is_file() and candidate.stat().st_size > 0:
                files.append(candidate)
    return files


def export_user_vocabulary(
    destination: Path,
    *,
    user_root: Path | None = None,
) -> Path:
    root = user_vocabulary_dir() if user_root is None else user_root
    files = collect_overlay_files(root)
    if not files:
        raise FileNotFoundError("No user vocabulary overlay to export.")

    destination = destination.expanduser()
    if destination.suffix.lower() != ".zip":
        destination = destination.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path.relative_to(root)))

    return destination
