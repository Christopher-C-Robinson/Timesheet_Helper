import remove_times
import timesheet_helper

# Place your bulleted timesheet here. The format is based on Microsoft Word bullets to be copy and pasted in here.
# You can use the following format:
timesheet = """
•	Monday
o	CR 12345 (Change Request 12345: Update sample user notification behavior) 8:30-2
o	Review PR 1234 (Example Task 12345: Updated sample automated test case for CR 12345 - 2510 branch) 2:15-3
o	Review PR 1234 (Pull Request 1234: Example Task 12345: Update sample automated tests for change request 12345) 3-4
o	Setup copilot 4-5
•	Tuesday
o	Research research 8-12:45
o	Example Task 12345 (Adds AI guidance docs for all workspace areas) 1-5:15
•	Wednesday
o	Review PR 1234-10
o	Chris - Mike 1:1 [In-person] 10-11
o	PTO (Personal) 1-5
•	Thursday
o	Research research 8:30-9
o	Engineering/Product 9-9:30
o	Addressing comment left of gh issue for testcafe fix for firefox and exampleapp site and app (https://github.com/DevExpress/testcafe/issues/8391) 9:30-11:45, 1-3
o	Harden pipeline test result scoping and cleanup 3-4
o	Review PR 1234 (Example Task 12345: Update sample automated tests for change request 12345) 4-5:15
•	Friday
o	Review PR 1234 (Pull Request 1234: Example Task 12345: Create sample automated test for bug 12345) 8:15-10
o	Test pipeline fixes 10-12:15, 1:15-4:30
o	PTO (Personal appointment) 4:30-6:30
"""

print("------------------------------------------------------------------------------------------------------------")
print(
    remove_times.remove_timespans(timesheet)
)  # Removes the timespans from the timesheet for email of what you did.
print("------------------------------------------------------------------------------------------------------------")
print(
    timesheet_helper.replace_with_duration(timesheet)
)  # Replaces the timespans with the duration of the timespans to be used for timesheet entry.
print("------------------------------------------------------------------------------------------------------------")
