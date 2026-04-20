import pytest
import timesheet_helper


def extract_hours(line):
    """Extract the numeric hour value from a task line like '• Task name 3.50\n'."""
    import re
    match = re.search(r'([\d.]+)\s*$', line.strip())
    return float(match.group(1)) if match else None


def extract_day_total(text, day_name):
    """Return the day total hours from the replace_with_duration output."""
    import re
    for line in text.split('\n'):
        m = re.search(rf'{day_name}.*Total:\s*([\d.]+)\s*hours', line)
        if m:
            return float(m.group(1))
    return None


def extract_weekly_total(text):
    """Return the weekly total hours from the replace_with_duration output."""
    import re
    m = re.search(r'Weekly Total:\s*([\d.]+)\s*hours', text)
    return float(m.group(1)) if m else None


def strip_ansi(text):
    """Remove ANSI escape codes from text."""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


def extract_task_hours(text, task_prefix):
    """Return the hours for the first task line starting with task_prefix."""
    import re
    for line in text.split('\n'):
        if task_prefix in line:
            m = re.search(r'([\d.]+)\s*$', line.strip())
            if m:
                return float(m.group(1))
    return None


def get_day_block(result, day_name):
    """Return lines belonging to the named day block (ANSI-stripped)."""
    import re
    lines = [strip_ansi(l) for l in result.split('\n')]
    in_block = False
    block = []
    for line in lines:
        if re.search(rf'\b{day_name}\b', line):
            in_block = True
        elif in_block and re.search(r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', line):
            in_block = False
        if in_block:
            block.append(line)
    return block


# ---------------------------------------------------------------------------
# Edge-case span tests
# ---------------------------------------------------------------------------

class TestTimespanEdgeCases:
    """Unit tests for individual time-span edge cases in replace_with_duration."""

    def _run_single_span(self, span):
        """Helper: build a minimal one-day timesheet with a single span and return hours."""
        text = f"• Monday\no Task {span}\n"
        result = timesheet_helper.replace_with_duration(text)
        return extract_task_hours(result, "Task")

    def test_same_hour_end_before_start_minutes(self):
        """12:45-12 should be 11.25 h (12:45 pm → midnight)."""
        hours = self._run_single_span("12:45-12")
        assert hours == pytest.approx(11.25), f"Expected 11.25 h, got {hours}"

    def test_one_to_twelve(self):
        """1-12 should be 11.0 h."""
        hours = self._run_single_span("1-12")
        assert hours == pytest.approx(11.0), f"Expected 11.0 h, got {hours}"

    def test_afternoon_crossover(self):
        """12:45-1:45 should be 1.0 h (end < start hour, existing logic)."""
        hours = self._run_single_span("12:45-1:45")
        assert hours == pytest.approx(1.0), f"Expected 1.0 h, got {hours}"

    def test_simple_morning_span(self):
        """8:45-12:15 should be 3.5 h."""
        hours = self._run_single_span("8:45-12:15")
        assert hours == pytest.approx(3.5), f"Expected 3.5 h, got {hours}"

    def test_afternoon_span(self):
        """1:45-5:15 should be 3.5 h."""
        hours = self._run_single_span("1:45-5:15")
        assert hours == pytest.approx(3.5), f"Expected 3.5 h, got {hours}"

    def test_cross_noon(self):
        """8-5 should be 9.0 h (end < start triggers +12)."""
        hours = self._run_single_span("8-5")
        assert hours == pytest.approx(9.0), f"Expected 9.0 h, got {hours}"

    def test_same_hour_end_after_start_minutes(self):
        """9-9:45 should be 0.75 h (end > start, no adjustment)."""
        hours = self._run_single_span("9-9:45")
        assert hours == pytest.approx(0.75), f"Expected 0.75 h, got {hours}"

    def test_twelve_to_one(self):
        """12-1 should be 1.0 h (end < start hour)."""
        hours = self._run_single_span("12-1")
        assert hours == pytest.approx(1.0), f"Expected 1.0 h, got {hours}"

    def test_nine_fortyfive_to_twelve(self):
        """9:45-12 should be 2.25 h."""
        hours = self._run_single_span("9:45-12")
        assert hours == pytest.approx(2.25), f"Expected 2.25 h, got {hours}"

    def test_comma_separated_spans(self):
        """Multiple spans on one task should sum correctly: 10-12, 1-12, 1-2 = 14 h."""
        hours = self._run_single_span("10-12, 1-12, 1-2")
        assert hours == pytest.approx(14.0), f"Expected 14.0 h, got {hours}"


# ---------------------------------------------------------------------------
# Full-sample acceptance-criteria tests
# ---------------------------------------------------------------------------

SAMPLE_TIMESHEET = """
• Monday
o QA Task 36119: Fix the broken tests that are related to the IFS Environment Destruction 8:45-12:15, 12:45-1:45
o SCIM testing 1:45-5:15
• Tuesday
o QA Task 36119: Fix the broken tests that are related to the IFS Environment Destruction 8:45-9, 9:45-12, 12:45-12
o Engineering/Product - additional until release 9-9:45
• Wednesday
o QA Task 36119: Fix the broken tests that are related to the IFS Environment Destruction 10:30-11:30. 12-5
o Review Pull Request 6002: Added Data Map Tests for SubmittedBy field in every data map 11:30-12
• Thursday
o Engineering/Product 9-10
o QA Task 36119: Fix the broken tests that are related to the IFS Environment Destruction 10-12, 1-12, 1-2
o Review Pull Request 6007: pipeline review 4/16 12-1
• Friday
o QA Task 36119: Fix the broken tests that are related to the IFS Environment Destruction 8-12
o Review Pull Request 6002: Added Data Map Tests for SubmittedBy field in every data map 1-5
"""


class TestAcceptanceCriteria:
    """Tests against the sample input from the issue's acceptance criteria."""

    @pytest.fixture(scope="class")
    def result(self):
        return timesheet_helper.replace_with_duration(SAMPLE_TIMESHEET)

    def test_tuesday_qa_task_hours(self, result):
        """Tuesday QA Task 36119 should be 13.75 h."""
        import re
        for line in get_day_block(result, "Tuesday"):
            if 'QA Task 36119' in line:
                m = re.search(r'([\d.]+)\s*$', line.strip())
                if m:
                    assert float(m.group(1)) == pytest.approx(13.75), \
                        f"Expected 13.75 h for Tuesday QA Task, got {m.group(1)}"
                    return
        pytest.fail("Tuesday QA Task 36119 line not found")

    def test_tuesday_total(self, result):
        """Total Tuesday should be 14.5 h."""
        total = extract_day_total(result, "Tuesday")
        assert total == pytest.approx(14.5), f"Expected 14.5 h for Tuesday total, got {total}"

    def test_thursday_qa_task_hours(self, result):
        """Thursday QA Task 36119 should be 14.0 h."""
        import re
        for line in get_day_block(result, "Thursday"):
            if 'QA Task 36119' in line:
                m = re.search(r'([\d.]+)\s*$', line.strip())
                if m:
                    assert float(m.group(1)) == pytest.approx(14.0), \
                        f"Expected 14.0 h for Thursday QA Task, got {m.group(1)}"
                    return
        pytest.fail("Thursday QA Task 36119 line not found")

    def test_thursday_total(self, result):
        """Total Thursday should be 16.0 h."""
        total = extract_day_total(result, "Thursday")
        assert total == pytest.approx(16.0), f"Expected 16.0 h for Thursday total, got {total}"
