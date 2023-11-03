import re

def remove_timespans(text):
    pattern = r"\b\d{1,2}(:\d{1,2})?-\d{1,2}(:\d{1,2})?\b,? *"
    result = re.sub(pattern, "", text)
    lines = result.split('\n')

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

    day_tasks = []
    output = []

    for line in lines:
        is_day_line = re.match(r'^\s*•\s*(\w+day)', line)
        if is_day_line:
            if day_tasks:
                output.append('\n'.join(day_tasks) + '\n')
                day_tasks = []
            day = re.sub(r'^\s*•\s*(\w+day)', r'\1', line)
            day = re.sub(r'(\w+day)', BOLD + UNDERLINE + r'\1' + END, day)
            day_tasks.append(day)
        else:
            task = re.sub(r'^\s*o\s*', '\t• ', line)
            day_tasks.append(task)

    if day_tasks:
        output.append('\n'.join(day_tasks) + '\n')

    result = '\n'.join(output)
    return result