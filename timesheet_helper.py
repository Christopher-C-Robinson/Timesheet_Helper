import re
from datetime import datetime, timedelta

def replace_with_duration(text):
    pattern = r"(\b\d{1,2})(:\d{1,2})?-(\d{1,2})(:\d{1,2})?\b"

    def duration(match):
        start_hour = int(match.group(1))
        start_minute = int(match.group(2)[1:]) if match.group(2) else 0
        end_hour = int(match.group(3))
        end_minute = int(match.group(4)[1:]) if match.group(4) else 0

        if end_hour < start_hour:
            end_hour += 12

        start = datetime(year=2000, month=1, day=1, hour=start_hour, minute=start_minute)
        end = datetime(year=2000, month=1, day=1, hour=end_hour, minute=end_minute)

        return end - start

    lines = text.split('\n')
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

    day_total_duration = timedelta()
    day_tasks = []
    output = []

    for line in lines:
        is_day_line = re.match(r'^\s*•\s*(\w+day)', line)
        if is_day_line:
            if day_tasks:
                day_tasks[0] += f' Total: {day_total_duration.total_seconds() / 3600:.2f}'
                output.append('\n'.join(day_tasks) + '\n')
                day_tasks = []

            day = re.sub(r'^\s*•\s*(\w+day)', r'\1', line)
            day = re.sub(r'(\w+day)', BOLD + UNDERLINE + r'\1' + END, day)
            day_tasks.append(day)
            day_total_duration = timedelta()
        else:
            timespans = re.finditer(pattern, line)
            total_duration = timedelta()
            for timespan in timespans:
                total_duration += duration(timespan)
                day_total_duration += duration(timespan)

            total_duration_hours = total_duration.total_seconds() / 3600
            total_duration_hours = "{:.2f}".format(total_duration_hours)

            if re.search(pattern, line):
                # Remove times and trailing commas
                task = re.sub(pattern + ',?', '', line).strip()
                task = re.sub(r'^\s*o\s*', '\t• ', task)
                task += f" {total_duration_hours}"
                day_tasks.append(task)

    if day_tasks:
        day_tasks[0] += f' Total: {day_total_duration.total_seconds() / 3600:.2f}'
        output.append('\n'.join(day_tasks) + '\n')

    result = '\n'.join(output)
    return result