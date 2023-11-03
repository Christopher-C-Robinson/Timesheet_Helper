import remove_times
import timesheet_helper

# Place your bulleted timesheet here. The format is based on microsoft word bullets to be copy and pasted in here. You can use the following format:
timesheet = """
•	Monday
o	task1 9:15-9:30, 10-12:15
o	task2 9:30-10
•	Tuesday
o	task1 9-9:30, 10:30-12:15
o	task2 9:30-10:30
•	Wednesday
o	task1 9-9:30, 10-12
o	task2 9:30-10
•	Thursday
o	task1 9-12
•	Friday
o	task1 9-9:30, 10-12
o	task2 9:30-10
"""

print('------------------------------------------------------------------------------------------------------------')
print(remove_times.remove_timespans(timesheet)) # Removes the timespans from the timesheet for email of what you did.
print('------------------------------------------------------------------------------------------------------------')
print(timesheet_helper.replace_with_duration(timesheet)) # Replaces the timespans with the duration of the timespans to be used for timesheet entry.
print('------------------------------------------------------------------------------------------------------------')