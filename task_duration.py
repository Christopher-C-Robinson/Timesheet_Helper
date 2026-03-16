import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List


TIME_PATTERN = r"(\b\d{1,2})(:\d{1,2})?-(\d{1,2})(:\d{1,2})?\b"
ROOT_DIR = Path(r"C:\Users\crobinson\OneDrive - OmniByte Technology, Inc\Weekly Updates")
WORK_ITEM = "scim"  # Set your ADO work item number here or Substring to match
EXTENSIONS = [".docx"]  # You can add ".txt" if you also store text copies
VERBOSE = False  # Set to True to see warnings and per-file info


def duration_from_line(line: str) -> timedelta:
    total = timedelta()
    for match in re.finditer(TIME_PATTERN, line):
        start_hour = int(match.group(1))
        start_minute = int(match.group(2)[1:]) if match.group(2) else 0
        end_hour = int(match.group(3))
        end_minute = int(match.group(4)[1:]) if match.group(4) else 0

        if end_hour < start_hour:
            end_hour += 12  # Afternoon handling (no midnight crossing assumed)

        start = datetime(year=2000, month=1, day=1, hour=start_hour, minute=start_minute)
        end = datetime(year=2000, month=1, day=1, hour=end_hour, minute=end_minute)
        total += end - start
    return total


def iter_files(root: Path, exts: Iterable[str]) -> Iterable[Path]:
    normalized_exts = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in exts}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith("~$"):  # Skip Word temp files
            continue
        if path.suffix.lower() in normalized_exts:
            yield path


def extract_lines(path: Path) -> List[str]:
    if path.suffix.lower() == ".docx":
        try:
            from docx import Document
        except ImportError as exc:  # pragma: no cover - import guard
            raise SystemExit(
                "Missing dependency: python-docx. "
                "Install it with 'python -m pip install python-docx'."
            ) from exc

        document = Document(path)
        return [para.text.strip() for para in document.paragraphs if para.text.strip()]

    # Fallback for plain text files
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip()]


def main() -> None:
    work_item_pattern = re.compile(rf"\b{re.escape(WORK_ITEM)}\b", re.IGNORECASE)
    total_duration = timedelta()
    matches_found = 0

    for file_path in iter_files(ROOT_DIR, EXTENSIONS):
        try:
            lines = extract_lines(file_path)
        except Exception as exc:  # pragma: no cover - defensive logging
            if VERBOSE:
                print(f"Warning: Failed to read {file_path}: {exc}")
            continue

        file_has_match = False
        for line in lines:
            if not work_item_pattern.search(line):
                continue

            line_duration = duration_from_line(line)
            if line_duration.total_seconds() == 0:
                if VERBOSE:
                    print(f"Warning: No time spans found in matched line: {file_path} | {line}")
                continue

            hours = line_duration.total_seconds() / 3600
            print(f"{file_path} | {line} | {hours:.2f} hours")
            total_duration += line_duration
            matches_found += 1
            file_has_match = True

        if VERBOSE and not file_has_match:
            print(f"Info: No matches in {file_path}")

    total_hours = total_duration.total_seconds() / 3600
    print("-" * 80)
    print(f"Total hours for work item {WORK_ITEM}: {total_hours:.2f}")
    print(f"Lines matched: {matches_found}")


if __name__ == "__main__":
    main()
