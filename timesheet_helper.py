import re
from datetime import datetime, timedelta

def replace_with_duration(text):
    """
    Replaces time durations in the given text with their corresponding durations in hours.

    Args:
        text (str): The input text containing time durations.

    Returns:
        str: The modified text with time durations replaced by their corresponding durations in hours.
    """
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
    weekly_total_duration = timedelta()
    day_tasks = []
    output = []

    for line in lines:
        is_day_line = re.match(r'^\s*•\s*(\w+day)', line)
        if is_day_line:
            if day_tasks:
                day_total_in_hours = day_total_duration.total_seconds() / 3600
                day_tasks[0] = day_tasks[0].rstrip() + f' Total: {day_total_in_hours:.2f} hours'
                output.append('\n'.join(day_tasks))
                weekly_total_duration += day_total_duration
                day_tasks = []
                day_total_duration = timedelta()

            day = re.sub(r'^\s*•\s*(\w+day)', r'\1', line)
            day = re.sub(r'(\w+day)', BOLD + UNDERLINE + r'\1' + END, day)
            output.append('')
            day_tasks.append(day)
        else:
            timespans = re.finditer(pattern, line)
            total_duration = timedelta()
            for timespan in timespans:
                span_duration = duration(timespan)
                total_duration += span_duration
                day_total_duration += span_duration

            total_duration_hours = total_duration.total_seconds() / 3600
            total_duration_hours = "{:.2f}".format(total_duration_hours)

            if re.search(pattern, line):
                task = re.sub(pattern + ',?', '', line).strip()
                task = re.sub(r'^\s*o\s*', '• ', task)
                task += f" {total_duration_hours}\n"  # Add a newline character here
                day_tasks.append(task)

    if day_tasks:
        day_total_in_hours = day_total_duration.total_seconds() / 3600
        total_string = f'Total: {day_total_in_hours:.2f} hours'
        day_string = day_tasks[0].ljust(20)  # Adjust the number as needed
        day_tasks[0] = day_string + total_string
        output.append('\n'.join(day_tasks))
        weekly_total_duration += day_total_duration

    weekly_total_hours = weekly_total_duration.total_seconds() / 3600
    output.append(f'\nWeekly Total: {weekly_total_hours:.2f} hours')

    result = '\n'.join(output)
    return result