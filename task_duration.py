import argparse
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import unquote, urlparse


TIME_PATTERN = r"(\b\d{1,2})(:\d{1,2})?-(\d{1,2})(:\d{1,2})?\b"
ROOT_DIR = Path(r"C:\Users\you\OneDrive - Example Org\Timesheet Notes")
WORK_ITEM = "12345"  # Set your ADO work item number here or Substring to match
EXTENSIONS = [".docx"]  # You can add ".txt" if you also store text copies
CLOUD_MODE = "word-refresh"  # Use "word-refresh", "trust-local", or "fail"
INCLUDE_UNSAVED_WORD = False  # Set True to include unsaved open Word document text
VERBOSE = False  # Set to True to see warnings and per-file info


class TaskDurationError(Exception):
    """Base error for intentional task-duration failures."""


class CloudTrustError(TaskDurationError):
    """Raised when cloud-backed files should not be trusted silently."""


class WordProviderError(TaskDurationError):
    """Raised when Word integration cannot provide the requested content."""


class AmbiguousWordDocumentError(TaskDurationError):
    """Raised when an open Word document cannot be matched safely."""


@dataclass(frozen=True)
class WordDocument:
    name: str
    full_name: str
    path: str
    saved: bool
    read_only: bool
    lines: List[str]


class WordProvider:
    def is_supported(self) -> bool:
        return False

    def list_open_documents(self) -> List[WordDocument]:
        return []

    def extract_readonly_document(self, path: Path) -> List[str]:
        raise WordProviderError("Microsoft Word automation is not supported on this platform.")


class WindowsPowerShellWordProvider(WordProvider):
    LIST_OPEN_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Get-DocumentLines($doc) {
    $lines = @()
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $text = $doc.Paragraphs.Item($i).Range.Text -replace "[`r`a]", ""
        $text = $text.Trim()
        if ($text.Length -gt 0) {
            $lines += $text
        }
    }
    return ,$lines
}

try {
    $word = [Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
} catch {
    ConvertTo-Json -InputObject @() -Depth 6 -Compress
    exit 0
}

$docs = @()
foreach ($doc in @($word.Documents)) {
    $docs += [pscustomobject]@{
        name = $doc.Name
        full_name = $doc.FullName
        path = $doc.Path
        saved = [bool]$doc.Saved
        read_only = [bool]$doc.ReadOnly
        lines = @(Get-DocumentLines $doc)
    }
}
ConvertTo-Json -InputObject $docs -Depth 6 -Compress
"""

    REFRESH_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$targetPath = $args[0]
$createdWord = $false
$word = $null
$doc = $null
$oldAlerts = $null
$wdDoNotSaveChanges = 0

function Get-DocumentLines($doc) {
    $lines = @()
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $text = $doc.Paragraphs.Item($i).Range.Text -replace "[`r`a]", ""
        $text = $text.Trim()
        if ($text.Length -gt 0) {
            $lines += $text
        }
    }
    return ,$lines
}

try {
    try {
        $word = [Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
    } catch {
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $createdWord = $true
    }

    $oldAlerts = $word.DisplayAlerts
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($targetPath, $false, $true)

    $result = [pscustomobject]@{
        lines = @(Get-DocumentLines $doc)
    }
    ConvertTo-Json -InputObject $result -Depth 6 -Compress
} finally {
    if ($null -ne $doc) {
        $doc.Close([ref]$wdDoNotSaveChanges)
    }
    if ($null -ne $word -and $null -ne $oldAlerts) {
        $word.DisplayAlerts = $oldAlerts
    }
    if ($createdWord -and $null -ne $word) {
        $word.Quit()
    }
}
"""

    def __init__(self) -> None:
        self.executable = shutil.which("powershell") or shutil.which("pwsh")

    def is_supported(self) -> bool:
        return self.executable is not None

    def _run(self, script: str, args: Sequence[str] = ()) -> object:
        if not self.executable:
            raise WordProviderError("PowerShell is required for Word automation on Windows.")

        completed = subprocess.run(
            [
                self.executable,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
                *args,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise WordProviderError(f"Word automation failed: {message}")

        output = completed.stdout.strip()
        if not output:
            return []
        return json.loads(output)

    def list_open_documents(self) -> List[WordDocument]:
        return decode_word_documents(self._run(self.LIST_OPEN_SCRIPT))

    def extract_readonly_document(self, path: Path) -> List[str]:
        result = self._run(self.REFRESH_SCRIPT, [str(path)])
        if not isinstance(result, dict):
            raise WordProviderError(f"Unexpected Word refresh response for {path}")
        return normalize_lines(result.get("lines", []))


class MacOsascriptWordProvider(WordProvider):
    LIST_OPEN_SCRIPT = r"""
function asLines(value) {
  return String(value || '').split(/\r|\n/).map(function (line) {
    return line.trim();
  }).filter(function (line) {
    return line.length > 0;
  });
}

function readText(doc) {
  try { return doc.content(); } catch (err) {}
  try { return doc.textObject.content(); } catch (err) {}
  return '';
}

function readFullName(doc) {
  try { return doc.fullName(); } catch (err) {}
  try { return doc.path(); } catch (err) {}
  return '';
}

function run(argv) {
  var word = Application('Microsoft Word');
  if (!word.running()) {
    return JSON.stringify([]);
  }
  var docs = word.documents();
  var result = docs.map(function (doc) {
    var fullName = readFullName(doc);
    var saved = true;
    try { saved = Boolean(doc.saved()); } catch (err) {}
    return {
      name: doc.name(),
      full_name: fullName,
      path: fullName,
      saved: saved,
      read_only: false,
      lines: asLines(readText(doc))
    };
  });
  return JSON.stringify(result);
}
"""

    REFRESH_SCRIPT = r"""
function asLines(value) {
  return String(value || '').split(/\r|\n/).map(function (line) {
    return line.trim();
  }).filter(function (line) {
    return line.length > 0;
  });
}

function readText(doc) {
  try { return doc.content(); } catch (err) {}
  try { return doc.textObject.content(); } catch (err) {}
  return '';
}

function run(argv) {
  var targetPath = argv[0];
  var word = Application('Microsoft Word');
  var doc = word.open(Path(targetPath), {readOnly: true});
  try {
    return JSON.stringify({ lines: asLines(readText(doc)) });
  } finally {
    try { doc.close({saving: 'no'}); } catch (err) {}
  }
}
"""

    def __init__(self) -> None:
        self.executable = shutil.which("osascript")

    def is_supported(self) -> bool:
        return self.executable is not None

    def _run(self, script: str, args: Sequence[str] = ()) -> object:
        if not self.executable:
            raise WordProviderError("osascript is required for Word automation on macOS.")

        completed = subprocess.run(
            [self.executable, "-l", "JavaScript", "-e", script, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise WordProviderError(f"Word automation failed: {message}")

        output = completed.stdout.strip()
        if not output:
            return []
        return json.loads(output)

    def list_open_documents(self) -> List[WordDocument]:
        return decode_word_documents(self._run(self.LIST_OPEN_SCRIPT))

    def extract_readonly_document(self, path: Path) -> List[str]:
        result = self._run(self.REFRESH_SCRIPT, [str(path)])
        if not isinstance(result, dict):
            raise WordProviderError(f"Unexpected Word refresh response for {path}")
        return normalize_lines(result.get("lines", []))


def provider_for_platform(platform_name: Optional[str] = None) -> WordProvider:
    platform_name = platform_name or sys.platform
    if platform_name.startswith("win"):
        return WindowsPowerShellWordProvider()
    if platform_name == "darwin":
        return MacOsascriptWordProvider()
    return WordProvider()


def normalize_lines(value: object) -> List[str]:
    if isinstance(value, str):
        candidates = re.split(r"\r\n|\r|\n", value)
    elif isinstance(value, list):
        candidates = [str(line) for line in value]
    elif value is None:
        candidates = []
    else:
        candidates = [str(value)]
    return [line.strip() for line in candidates if line.strip()]


def decode_word_documents(value: object) -> List[WordDocument]:
    if isinstance(value, dict):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        raise WordProviderError("Unexpected Word document list response.")

    documents = []
    for item in items:
        if not isinstance(item, dict):
            continue
        documents.append(
            WordDocument(
                name=str(item.get("name", "")),
                full_name=str(item.get("full_name", "")),
                path=str(item.get("path", "")),
                saved=bool(item.get("saved", True)),
                read_only=bool(item.get("read_only", False)),
                lines=normalize_lines(item.get("lines", [])),
            )
        )
    return documents


def duration_from_line(line: str) -> timedelta:
    total = timedelta()
    for match in re.finditer(TIME_PATTERN, line):
        start_hour = int(match.group(1))
        start_minute = int(match.group(2)[1:]) if match.group(2) else 0
        end_hour = int(match.group(3))
        end_minute = int(match.group(4)[1:]) if match.group(4) else 0

        start = datetime(year=2000, month=1, day=1, hour=start_hour, minute=start_minute)
        end = datetime(year=2000, month=1, day=1, hour=end_hour, minute=end_minute)
        if end < start:
            end += timedelta(hours=12)  # Afternoon handling (no midnight crossing assumed)
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


def extract_lines_from_disk(path: Path) -> List[str]:
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

    text = path.read_text(encoding="utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_lines(path: Path) -> List[str]:
    """Compatibility wrapper for disk-only extraction."""
    return extract_lines_from_disk(path)


def comparable_text(value: object) -> str:
    return unquote(str(value)).replace("\\", "/").rstrip("/").casefold()


def path_is_under(child: object, parent: object) -> bool:
    child_text = comparable_text(child)
    parent_text = comparable_text(parent)
    return child_text == parent_text or child_text.startswith(parent_text + "/")


def split_comparable_parts(value: object) -> Tuple[str, ...]:
    text = str(value)
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https", "file"}:
        text = parsed.path
    text = unquote(text).replace("\\", "/")
    return tuple(part.casefold() for part in text.split("/") if part)


def endswith_parts(parts: Tuple[str, ...], suffix: Tuple[str, ...]) -> bool:
    return bool(suffix) and len(parts) >= len(suffix) and parts[-len(suffix) :] == suffix


def tail_after_marker(parts: Tuple[str, ...], marker: str) -> Tuple[str, ...]:
    marker = marker.casefold()
    if marker not in parts:
        return ()
    index = len(parts) - 1 - tuple(reversed(parts)).index(marker)
    return parts[index + 1 :]


def path_has_reparse_point(path: Path) -> bool:
    if os.name != "nt":
        return False

    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if not reparse_flag:
        return False

    candidates = [path, *path.parents]
    for candidate in candidates:
        try:
            attributes = getattr(candidate.stat(), "st_file_attributes", 0)
        except OSError:
            continue
        if attributes & reparse_flag:
            return True
    return False


def is_cloud_backed_path(
    path: Path,
    platform_name: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    reparse_checker: Optional[Callable[[Path], bool]] = None,
) -> bool:
    platform_name = platform_name or sys.platform
    env = os.environ if env is None else env
    reparse_checker = path_has_reparse_point if reparse_checker is None else reparse_checker

    parts = split_comparable_parts(path)
    if any(part == "onedrive" or part.startswith("onedrive -") for part in parts):
        return True

    comparable = comparable_text(path)
    if "/library/cloudstorage/onedrive-" in comparable:
        return True

    if platform_name.startswith("win"):
        for key in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
            root = env.get(key)
            if root and path_is_under(path, root):
                return True
        if reparse_checker(path):
            return True

    if platform_name == "darwin":
        for key in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
            root = env.get(key)
            if root and path_is_under(path, root):
                return True

    return False


def document_match_score(path: Path, document: WordDocument) -> int:
    target_parts = split_comparable_parts(path)
    target_name = path.name.casefold()
    scores = []

    for value in (document.full_name, document.path):
        if not value:
            continue
        doc_parts = split_comparable_parts(value)
        if comparable_text(value) == comparable_text(path):
            scores.append(100)
        if endswith_parts(target_parts, doc_parts) or endswith_parts(doc_parts, target_parts):
            scores.append(90)

        # SharePoint-backed Word docs often expose a URL under /Documents/
        # while the local OneDrive path starts at that document-library child.
        documents_tail = tail_after_marker(doc_parts, "documents")
        if endswith_parts(target_parts, documents_tail):
            scores.append(80)

    if document.name.casefold() == target_name:
        scores.append(10)

    return max(scores) if scores else 0


class DocumentResolver:
    def __init__(
        self,
        cloud_mode: str,
        include_unsaved_word: bool = False,
        verbose: bool = False,
        word_provider: Optional[WordProvider] = None,
        disk_extractor: Callable[[Path], List[str]] = extract_lines_from_disk,
        cloud_detector: Callable[[Path], bool] = is_cloud_backed_path,
    ) -> None:
        self.cloud_mode = cloud_mode
        self.include_unsaved_word = include_unsaved_word
        self.verbose = verbose
        self.word_provider = provider_for_platform() if word_provider is None else word_provider
        self.disk_extractor = disk_extractor
        self.cloud_detector = cloud_detector
        self._open_documents_loaded = False
        self._open_documents: List[WordDocument] = []

    def _load_open_documents(self) -> List[WordDocument]:
        if self._open_documents_loaded:
            return self._open_documents

        self._open_documents_loaded = True
        if not self.word_provider.is_supported():
            self._open_documents = []
            return self._open_documents

        try:
            self._open_documents = self.word_provider.list_open_documents()
        except WordProviderError:
            if self.cloud_mode == "word-refresh":
                raise
            self._open_documents = []
        return self._open_documents

    def find_open_document(self, path: Path) -> Optional[WordDocument]:
        candidates = []
        for document in self._load_open_documents():
            score = document_match_score(path, document)
            if score > 0:
                candidates.append((score, document))

        if not candidates:
            return None

        top_score = max(score for score, _ in candidates)
        top_documents = [document for score, document in candidates if score == top_score]
        if len(top_documents) > 1:
            matches = ", ".join(document.full_name or document.name for document in top_documents)
            raise AmbiguousWordDocumentError(
                f"Ambiguous open Word document match for {path}: {matches}"
            )
        return top_documents[0]

    def extract_lines(self, path: Path) -> Tuple[List[str], str]:
        if path.suffix.lower() != ".docx":
            return self.disk_extractor(path), "disk"

        open_document = self.find_open_document(path)
        if open_document is not None:
            if not open_document.saved and not self.include_unsaved_word:
                raise WordProviderError(
                    f"{path} is open in Word with unsaved changes. "
                    "Save it or rerun with --include-unsaved-word to read the live unsaved text."
                )
            return open_document.lines, "word-open"

        if self.cloud_mode == "word-refresh":
            if not self.word_provider.is_supported():
                raise WordProviderError(
                    "Microsoft Word automation is required for --cloud-mode word-refresh "
                    "on .docx files."
                )
            return self.word_provider.extract_readonly_document(path), "word-refreshed"

        return self.disk_extractor(path), "disk"


def cloud_warning(root: Path, files: Sequence[Path]) -> str:
    return (
        f"Cloud-backed path detected under {root}.\n"
        "Refusing to read possibly stale OneDrive files in --cloud-mode fail.\n"
        "Verify OneDrive says the folder is up to date, then rerun with "
        "--cloud-mode word-refresh to read through Microsoft Word or "
        "--cloud-mode trust-local to use the local disk copies.\n"
        "No local script can detect edits that another machine has not uploaded yet."
    )


def validate_cloud_mode(
    root: Path,
    files: Sequence[Path],
    cloud_mode: str,
    cloud_detector: Callable[[Path], bool] = is_cloud_backed_path,
) -> bool:
    cloud_backed = cloud_detector(root) or any(cloud_detector(file_path) for file_path in files)
    if cloud_backed and cloud_mode == "fail":
        raise CloudTrustError(cloud_warning(root, files))
    return cloud_backed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sum task durations from Word/text timesheet files."
    )
    parser.add_argument(
        "--work-item",
        default=WORK_ITEM,
        help="Work item number or exact token to match. Defaults to WORK_ITEM in the script.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT_DIR,
        help="Root folder to scan for timesheet files.",
    )
    parser.add_argument(
        "--cloud-mode",
        choices=("fail", "trust-local", "word-refresh"),
        default=CLOUD_MODE,
        help=(
            "How to handle OneDrive/cloud-backed files: fail, trust local disk copies, "
            "or read .docx files through Microsoft Word."
        ),
    )
    parser.add_argument(
        "--include-unsaved-word",
        action="store_true",
        default=INCLUDE_UNSAVED_WORD,
        help="Read live open Word documents even when Word reports unsaved changes.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=VERBOSE,
        help="Show warnings, per-file source info, and no-match diagnostics.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root
    verbose = bool(args.verbose)
    work_item_pattern = re.compile(rf"\b{re.escape(args.work_item)}\b", re.IGNORECASE)

    try:
        files = list(iter_files(root, EXTENSIONS))
        cloud_backed = validate_cloud_mode(root, files, args.cloud_mode)
        if cloud_backed and args.cloud_mode in {"trust-local", "word-refresh"}:
            print(
                "Warning: cloud-backed files detected. This machine can only read content "
                "that has already synced from other devices.",
                file=sys.stderr,
            )
    except TaskDurationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    resolver = DocumentResolver(
        cloud_mode=args.cloud_mode,
        include_unsaved_word=args.include_unsaved_word,
        verbose=verbose,
    )

    total_duration = timedelta()
    matches_found = 0

    for file_path in files:
        try:
            lines, source = resolver.extract_lines(file_path)
        except TaskDurationError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:  # pragma: no cover - defensive logging
            if verbose:
                print(f"Warning: Failed to read {file_path}: {exc}")
            continue

        file_has_match = False
        for line in lines:
            if not work_item_pattern.search(line):
                continue

            line_duration = duration_from_line(line)
            if line_duration.total_seconds() == 0:
                if verbose:
                    print(f"Warning: No time spans found in matched line: {file_path} | {line}")
                continue

            hours = line_duration.total_seconds() / 3600
            prefix = f"{file_path} [{source}]" if verbose else str(file_path)
            print(f"{prefix} | {line} | {hours:.2f} hours")
            total_duration += line_duration
            matches_found += 1
            file_has_match = True

        if verbose and not file_has_match:
            print(f"Info: No matches in {file_path}")

    total_hours = total_duration.total_seconds() / 3600
    print("-" * 80)
    print(f"Total hours for work item {args.work_item}: {total_hours:.2f}")
    print(f"Lines matched: {matches_found}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
