import re

from duration_parser import parse_duration


def replace_with_duration(text):
    """Render task durations from submitted totals or legacy time ranges."""
    lines = text.split("\n")
    BOLD, UNDERLINE, END = "\033[1m", "\033[4m", "\033[0m"
    day_total_hours = weekly_total_hours = 0.0
    day_tasks, output = [], []

    for line in lines:
        if re.match(r"^\s*•\s*(\w+day)", line):
            if day_tasks:
                day_tasks[0] = day_tasks[0].rstrip() + f" Total: {day_total_hours:.2f} hours"
                output.append("\n".join(day_tasks))
                weekly_total_hours += day_total_hours
                day_tasks, day_total_hours = [], 0.0
            day = re.sub(r"^\s*•\s*(\w+day)", r"\1", line)
            day_tasks.append(re.sub(r"(\w+day)", BOLD + UNDERLINE + r"\1" + END, day))
            output.append("")
            continue
        parsed = parse_duration(line)
        if parsed is None:
            continue
        task = re.sub(r"^\s*o\s*", "• ", parsed.task_text).strip()
        day_tasks.append(f"{task} {parsed.hours:.2f}\n")
        day_total_hours += parsed.hours

    if day_tasks:
        day_tasks[0] = day_tasks[0].rstrip() + f" Total: {day_total_hours:.2f} hours"
        output.append("\n".join(day_tasks))
        weekly_total_hours += day_total_hours
    output.append(f"\nWeekly Total: {weekly_total_hours:.2f} hours")
    return "\n".join(output)
