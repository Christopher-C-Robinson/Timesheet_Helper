import re

from duration_parser import strip_duration_annotations


def remove_timespans(text):
    """Format a timesheet for email without time ranges or submitted totals."""
    BOLD, UNDERLINE, END = "\033[1m", "\033[4m", "\033[0m"
    day_tasks, output = [], []
    for line in text.split("\n"):
        if re.match(r"^\s*•\s*(\w+day)", line):
            if day_tasks:
                output.append("\n".join(day_tasks) + "\n")
                day_tasks = []
            day = re.sub(r"^\s*•\s*(\w+day)", r"\1", line)
            day_tasks.append(re.sub(r"(\w+day)", BOLD + UNDERLINE + r"\1" + END, day))
            continue
        task = re.sub(r"^\s*o\s*", "\t• ", strip_duration_annotations(line))
        day_tasks.append(task)
    if day_tasks:
        output.append("\n".join(day_tasks) + "\n")
    return "\n".join(output)
