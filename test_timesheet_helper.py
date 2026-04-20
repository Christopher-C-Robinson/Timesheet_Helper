import re
import pytest
import timesheet_helper
import task_duration
import remove_times


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

    def test_period_separated_spans(self):
        """Spans separated by a period should sum: 10:30-11:30. 12-5 = 6 h."""
        hours = self._run_single_span("10:30-11:30. 12-5")
        assert hours == pytest.approx(6.0), f"Expected 6.0 h, got {hours}"

    def test_period_separated_spans_no_period_in_output(self):
        """Task name must not contain a leftover standalone period after spans are stripped."""
        text = "• Monday\no Task 10:30-11:30. 12-5\n"
        result = timesheet_helper.replace_with_duration(text)
        clean = re.sub(r'\033\[[0-9;]*m', '', result)
        for line in clean.split('\n'):
            if 'Task' in line:
                # A leftover separator period appears as ` . ` (space-period-space) before the hours
                assert not re.search(r'\s\.\s', line), \
                    f"Leftover standalone period in task line: {repr(line)}"
                break


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

    def test_wednesday_qa_task_no_leftover_period(self, result):
        """Wednesday QA task line (with period-separated spans) must not contain a leftover period."""
        for line in get_day_block(result, "Wednesday"):
            if 'QA Task 36119' in line:
                # A leftover separator period appears as ' . ' (space-period-space) before hours
                assert not re.search(r'\s\.\s', line), \
                    f"Leftover standalone period in Wednesday task: {repr(line)}"
                return
        pytest.fail("Wednesday QA Task 36119 line not found")


# ---------------------------------------------------------------------------
# task_duration.duration_from_line edge-case tests
# ---------------------------------------------------------------------------


class TestTaskDurationFromLine:
    """Unit tests for task_duration.duration_from_line edge cases."""

    def _hours(self, span: str) -> float:
        """Return hours for a single time span embedded in a task line."""
        return task_duration.duration_from_line(f"Some Task {span}").total_seconds() / 3600

    def test_same_hour_end_before_start_minutes(self):
        """12:45-12 should be 11.25 h (end minutes < start minutes, same hour)."""
        assert self._hours("12:45-12") == pytest.approx(11.25)

    def test_one_to_twelve(self):
        """1-12 should be 11.0 h (end > start, no afternoon adjustment needed)."""
        assert self._hours("1-12") == pytest.approx(11.0)

    def test_twelve_to_one(self):
        """12-1 should be 1.0 h (end < start triggers +12)."""
        assert self._hours("12-1") == pytest.approx(1.0)

    def test_afternoon_crossover(self):
        """12:45-1:45 should be 1.0 h."""
        assert self._hours("12:45-1:45") == pytest.approx(1.0)

    def test_simple_morning_span(self):
        """8:45-12:15 should be 3.5 h."""
        assert self._hours("8:45-12:15") == pytest.approx(3.5)

    def test_cross_noon(self):
        """8-5 should be 9.0 h (end < start triggers +12)."""
        assert self._hours("8-5") == pytest.approx(9.0)

    def test_nine_fortyfive_to_twelve(self):
        """9:45-12 should be 2.25 h."""
        assert self._hours("9:45-12") == pytest.approx(2.25)

    def test_comma_separated_spans(self):
        """10-12, 1-12, 1-2 should sum to 14.0 h."""
        assert self._hours("10-12, 1-12, 1-2") == pytest.approx(14.0)


# ---------------------------------------------------------------------------
# remove_times.remove_timespans tests
# ---------------------------------------------------------------------------


class TestRemoveTimes:
    """Unit tests for remove_times.remove_timespans separator cleanup."""

    def _strip_ansi(self, text):
        return re.sub(r'\033\[[0-9;]*m', '', text)

    def test_period_separator_removed(self):
        """Period between spans (e.g. '10:30-11:30. 12-5') must not appear in output."""
        text = "• Wednesday\no QA Task 10:30-11:30. 12-5\n"
        result = self._strip_ansi(remove_times.remove_timespans(text))
        for line in result.split('\n'):
            if 'QA Task' in line:
                assert '.' not in line, f"Leftover period in remove_timespans output: {repr(line)}"
                return
        pytest.fail("QA Task line not found in remove_timespans output")

    def test_comma_separator_removed(self):
        """Comma between spans must not appear in output."""
        text = "• Monday\no Task 8:45-9, 9:45-12\n"
        result = self._strip_ansi(remove_times.remove_timespans(text))
        for line in result.split('\n'):
            if 'Task' in line:
                assert ',' not in line, f"Leftover comma in remove_timespans output: {repr(line)}"
                return
        pytest.fail("Task line not found in remove_timespans output")
