"""Shared parsing for legacy time ranges and submitted source-hour totals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional, Tuple


TIME_RANGE_PATTERN = re.compile(r"(\b\d{1,2})(:\d{1,2})?-(\d{1,2})(:\d{1,2})?\b")
TIME_RANGE_WITH_SEPARATOR_PATTERN = re.compile(
    r"\b\d{1,2}(?::\d{1,2})?-\d{1,2}(?::\d{1,2})?\b[,.]?\s*"
)
SUBMITTED_HOURS_PATTERN = re.compile(
    r"\s[-\u2013\u2014]\s*(\d+(?:\.\d+)?)\s*(?:hrs?|hours?)\s*$",
    re.IGNORECASE,
)
WORK_ITEM_REFERENCE_PATTERN = re.compile(
    r"\b(?:QA\s+)?(?:Task|Bug|Defect|User\s+Story|Pull\s+Request|PR)\s*#?\s*(\d{4,})\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedDuration:
    hours: float
    source: Literal["submitted-total", "time-ranges"]
    task_text: str


def duration_from_time_ranges(text: str) -> timedelta:
    total = timedelta()
    for match in TIME_RANGE_PATTERN.finditer(text):
        start = datetime(2000, 1, 1, int(match.group(1)), int(match.group(2)[1:]) if match.group(2) else 0)
        end = datetime(2000, 1, 1, int(match.group(3)), int(match.group(4)[1:]) if match.group(4) else 0)
        if end < start:
            end += timedelta(hours=12)
        total += end - start
    return total


def strip_time_ranges(text: str) -> str:
    return TIME_RANGE_WITH_SEPARATOR_PATTERN.sub("", text).strip()


def strip_duration_annotations(text: str) -> str:
    submitted_match = SUBMITTED_HOURS_PATTERN.search(text)
    if submitted_match:
        text = text[: submitted_match.start()]
    return strip_time_ranges(text)


def parse_duration(text: str) -> Optional[ParsedDuration]:
    submitted_match = SUBMITTED_HOURS_PATTERN.search(text)
    if submitted_match:
        return ParsedDuration(
            hours=float(submitted_match.group(1)),
            source="submitted-total",
            task_text=strip_time_ranges(text[: submitted_match.start()]),
        )
    duration = duration_from_time_ranges(text)
    if duration.total_seconds() == 0:
        return None
    return ParsedDuration(
        hours=duration.total_seconds() / 3600,
        source="time-ranges",
        task_text=strip_time_ranges(text),
    )


def referenced_work_item_ids(text: str) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(WORK_ITEM_REFERENCE_PATTERN.findall(text)))
