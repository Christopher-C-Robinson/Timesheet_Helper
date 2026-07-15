from pathlib import Path

import pytest

import duration_parser
import remove_times
import task_duration
import timesheet_helper


@pytest.mark.parametrize("suffix", ["- 8.75 hr", "– 8.75 hrs", "— 8.75 hour", "- 8.75 hours"])
def test_terminal_submitted_total_variants(suffix):
    parsed = duration_parser.parse_duration(f"o QA Task 12345: recovered work {suffix}")
    assert parsed is not None
    assert parsed.source == "submitted-total"
    assert parsed.hours == pytest.approx(8.75)


def test_submitted_total_overrides_ranges_and_helpers_clean_it():
    text = "\u2022 Monday\no QA Task 12345: work 9-10, 10:15-11 – 8.75 hrs\n"
    parsed = duration_parser.parse_duration(text.splitlines()[1])
    assert parsed is not None and parsed.hours == pytest.approx(8.75)
    duration_output = timesheet_helper.replace_with_duration(text)
    email_output = remove_times.remove_timespans(text)
    assert "8.75" in duration_output
    assert "Weekly Total: 8.75 hours" in duration_output
    assert "8.75" not in email_output
    assert "9-10" not in email_output


def test_legacy_range_is_still_used_when_no_submitted_total():
    parsed = duration_parser.parse_duration("o QA Task 12345: work 9-10, 10:15-11")
    assert parsed is not None
    assert parsed.source == "time-ranges"
    assert parsed.hours == pytest.approx(1.75)


def test_backup_folder_is_excluded_unless_requested(tmp_path):
    active = tmp_path / "Week 29.txt"
    active.write_text("QA Task 12345 - 1 hrs", encoding="utf-8")
    backup = tmp_path / "Backup Before Reconciliation - 2026-07-15" / "Week 29.txt"
    backup.parent.mkdir()
    backup.write_text("QA Task 12345 - 8 hrs", encoding="utf-8")
    assert list(task_duration.iter_files(tmp_path, [".txt"])) == [active]
    assert set(task_duration.iter_files(tmp_path, [".txt"], include_backups=True)) == {active, backup}


def test_shared_source_totals_are_identified_conservatively():
    assert task_duration.is_shared_submitted_total(
        "QA Task #12345 and Pull Request 23456 - 4.50 hours", "12345"
    )
    assert not task_duration.is_shared_submitted_total(
        "QA Task 12345, related note 23456 - 4.50 hours", "12345"
    )
    assert not task_duration.is_shared_submitted_total(
        "QA Task 12345 and Bug 23456 9-10", "12345"
    )


def test_main_reports_strict_and_shared_override(tmp_path, monkeypatch, capsys):
    source = tmp_path / "week.txt"
    source.write_text(
        "QA Task 12345: individual - 2.50 hrs\n"
        "QA Task 12345 and Bug 23456: combined - 4.00 hrs\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(task_duration, "EXTENSIONS", [".txt"])
    assert task_duration.main(["--work-item", "12345", "--root", str(tmp_path), "--cloud-mode", "trust-local"]) == 0
    strict = capsys.readouterr().out
    assert "Exact total for work item 12345: 2.50" in strict
    assert "Potential total including shared source rows: 6.50" in strict
    assert task_duration.main(["--work-item", "12345", "--root", str(tmp_path), "--cloud-mode", "trust-local", "--include-shared-totals"]) == 0
    inclusive = capsys.readouterr().out
    assert "including shared source totals): 6.50" in inclusive
