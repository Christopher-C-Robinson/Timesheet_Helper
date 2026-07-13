from pathlib import Path

import pytest

import task_duration


class FakeWordProvider(task_duration.WordProvider):
    def __init__(self, open_documents=None, refreshed_lines=None, supported=True):
        self.open_documents = open_documents or []
        self.refreshed_lines = refreshed_lines or ["refreshed"]
        self.supported = supported
        self.refreshed_paths = []

    def is_supported(self):
        return self.supported

    def list_open_documents(self):
        return self.open_documents

    def extract_readonly_document(self, path):
        self.refreshed_paths.append(path)
        return self.refreshed_lines


def make_doc(path, lines=None, saved=True, name=None, full_name=None):
    return task_duration.WordDocument(
        name=name or Path(path).name,
        full_name=full_name or str(path),
        path=full_name or str(path),
        saved=saved,
        read_only=False,
        lines=lines or ["word-open"],
    )


def test_detects_windows_onedrive_path():
    path = Path(r"C:\Users\me\OneDrive - Example Org\Timesheet Notes")

    assert task_duration.is_cloud_backed_path(
        path,
        platform_name="win32",
        env={},
        reparse_checker=lambda _: False,
    )


def test_detects_windows_onedrive_env_root():
    path = Path(r"C:\Users\me\CompanyDrive\Timesheet Notes\week.docx")

    assert task_duration.is_cloud_backed_path(
        path,
        platform_name="win32",
        env={"OneDriveCommercial": r"C:\Users\me\CompanyDrive"},
        reparse_checker=lambda _: False,
    )


def test_detects_macos_onedrive_cloudstorage_path():
    path = Path("/Users/me/Library/CloudStorage/OneDrive-ExampleOrg/Timesheet Notes/week.docx")

    assert task_duration.is_cloud_backed_path(
        path,
        platform_name="darwin",
        env={},
        reparse_checker=lambda _: False,
    )


def test_normal_local_path_is_not_cloud_backed():
    path = Path(r"C:\Code\Timesheets\week.docx")

    assert not task_duration.is_cloud_backed_path(
        path,
        platform_name="win32",
        env={},
        reparse_checker=lambda _: False,
    )


def test_reparse_point_marks_windows_path_cloud_backed():
    path = Path(r"C:\Users\me\Documents\week.docx")

    assert task_duration.is_cloud_backed_path(
        path,
        platform_name="win32",
        env={},
        reparse_checker=lambda _: True,
    )


def test_open_saved_word_document_is_authoritative():
    path = Path(r"C:\Users\me\OneDrive - Org\Timesheet Notes\week.docx")
    provider = FakeWordProvider(open_documents=[make_doc(path, lines=["live text"])])
    resolver = task_duration.DocumentResolver(
        cloud_mode="trust-local",
        word_provider=provider,
        disk_extractor=lambda _: ["disk text"],
    )

    lines, source = resolver.extract_lines(path)

    assert lines == ["live text"]
    assert source == "word-open"


def test_open_unsaved_word_document_fails_by_default():
    path = Path(r"C:\Users\me\OneDrive - Org\Timesheet Notes\week.docx")
    provider = FakeWordProvider(open_documents=[make_doc(path, saved=False)])
    resolver = task_duration.DocumentResolver(
        cloud_mode="trust-local",
        word_provider=provider,
        disk_extractor=lambda _: ["disk text"],
    )

    with pytest.raises(task_duration.WordProviderError, match="unsaved changes"):
        resolver.extract_lines(path)


def test_open_unsaved_word_document_can_be_included():
    path = Path(r"C:\Users\me\OneDrive - Org\Timesheet Notes\week.docx")
    provider = FakeWordProvider(open_documents=[make_doc(path, lines=["unsaved"], saved=False)])
    resolver = task_duration.DocumentResolver(
        cloud_mode="trust-local",
        include_unsaved_word=True,
        word_provider=provider,
        disk_extractor=lambda _: ["disk text"],
    )

    lines, source = resolver.extract_lines(path)

    assert lines == ["unsaved"]
    assert source == "word-open"


def test_word_refresh_opens_closed_doc_readonly():
    path = Path(r"C:\Users\me\OneDrive - Org\Timesheet Notes\week.docx")
    provider = FakeWordProvider(open_documents=[], refreshed_lines=["fresh text"])
    resolver = task_duration.DocumentResolver(
        cloud_mode="word-refresh",
        word_provider=provider,
        disk_extractor=lambda _: ["disk text"],
    )

    lines, source = resolver.extract_lines(path)

    assert lines == ["fresh text"]
    assert source == "word-refreshed"
    assert provider.refreshed_paths == [path]


def test_trust_local_reads_disk_for_closed_doc():
    path = Path(r"C:\Users\me\OneDrive - Org\Timesheet Notes\week.docx")
    provider = FakeWordProvider(open_documents=[])
    resolver = task_duration.DocumentResolver(
        cloud_mode="trust-local",
        word_provider=provider,
        disk_extractor=lambda _: ["disk text"],
    )

    lines, source = resolver.extract_lines(path)

    assert lines == ["disk text"]
    assert source == "disk"


def test_cloud_fail_rejects_cloud_backed_files_before_reading():
    root = Path(r"C:\Users\me\OneDrive - Org\Timesheet Notes")
    file_path = root / "week.docx"

    with pytest.raises(task_duration.CloudTrustError):
        task_duration.validate_cloud_mode(
            root,
            [file_path],
            "fail",
            cloud_detector=lambda _: True,
        )


def test_sharepoint_url_maps_to_local_onedrive_path():
    path = Path(
        r"C:\Users\me\OneDrive - Example Org\Timesheet Notes\2026"
        r"\Week 25 2026 Weekly Update.docx"
    )
    full_name = (
        "https://example-my.sharepoint.com/personal/me/Documents/"
        "Weekly%20Updates/2026/Week%2025%202026%20Weekly%20Update.docx"
    )
    provider = FakeWordProvider(open_documents=[make_doc(path, full_name=full_name)])
    resolver = task_duration.DocumentResolver(
        cloud_mode="trust-local",
        word_provider=provider,
        disk_extractor=lambda _: ["disk text"],
    )

    assert resolver.find_open_document(path) == provider.open_documents[0]


def test_duplicate_filename_open_docs_are_ambiguous():
    target = Path(r"C:\Timesheets\Week 25 2026 Weekly Update.docx")
    docs = [
        make_doc(target, full_name="https://example.com/Documents/A/Week%2025%202026%20Weekly%20Update.docx"),
        make_doc(target, full_name="https://example.com/Documents/B/Week%2025%202026%20Weekly%20Update.docx"),
    ]
    provider = FakeWordProvider(open_documents=docs)
    resolver = task_duration.DocumentResolver(
        cloud_mode="trust-local",
        word_provider=provider,
        disk_extractor=lambda _: ["disk text"],
    )

    with pytest.raises(task_duration.AmbiguousWordDocumentError):
        resolver.find_open_document(target)
