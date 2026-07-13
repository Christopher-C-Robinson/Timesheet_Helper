import remove_times
import timesheet_helper

# Place your bulleted timesheet here. The format is based on Microsoft Word bullets to be copy and pasted in here.
# You can use the following format:
timesheet = (
    "\u2022 Monday\n"
    "o Feature planning 8:30-10\n"
    "o Task 12345: Build sample reporting workflow 10-12, 1-3\n"
    "o Review PR 1234: Update sample automation coverage 3:15-4\n"
    "o Team sync 4-5\n"
    "\u2022 Tuesday\n"
    "o Task 12345: Continue sample reporting workflow 8:45-12\n"
    "o Integration testing 1-3:30\n"
    "o Documentation updates 3:30-5\n"
    "\u2022 Wednesday\n"
    "o Review PR 1234: Refine example validation 9-10\n"
    "o Task 12345: Investigate sample defect 10-12, 1-4\n"
    "\u2022 Thursday\n"
    "o Product support 8:30-9:30\n"
    "o Task 12345: Finish sample reporting workflow 9:30-12, 1-3\n"
    "o Release notes 3-4:30\n"
    "\u2022 Friday\n"
    "o Regression testing 8:30-11:30\n"
    "o Personal time 1-5\n"
)

print("------------------------------------------------------------------------------------------------------------")
print(
    remove_times.remove_timespans(timesheet)
)  # Removes the timespans from the timesheet for email of what you did.
print("------------------------------------------------------------------------------------------------------------")
print(
    timesheet_helper.replace_with_duration(timesheet)
)  # Replaces the timespans with the duration of the timespans to be used for timesheet entry.
print("------------------------------------------------------------------------------------------------------------")
