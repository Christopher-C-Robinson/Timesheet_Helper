import remove_times
import timesheet_helper

# Place your bulleted timesheet here. The format is based on Microsoft Word bullets to be copy and pasted in here.
# You can use the following format:
timesheet = """
•	Monday
o	CR 34754 (Change Request 34754: Requesting for all popup toast messages to have a dismiss button on them) 8:30-2
o	Review PR 5788 (QA Task 35397: Updated Automated Test case for CR 35204 - 2510 branch) 2:15-3
o	Review PR 5779 (Pull Request 5779: QA Task 35355: Update Automated Test Cases for Change Request 35204) 3-4
o	Setup copilot 4-5
•	Tuesday
o	SKIM research 8-12:45
o	Dev Task 35491 (Adds AI guidance docs for all workspace areas) 1-5:15
•	Wednesday
o	Review PR 9-10
o	Chris - Mike 1:1 [In-person] 10-11
o	PTO (Personal) 1-5
•	Thursday
o	SKIM research 8:30-9
o	Engineering/Product 9-9:30
o	Addressing comment left of gh issue for testcafe fix for firefox and formspro site and app (https://github.com/DevExpress/testcafe/issues/8391) 9:30-11:45, 1-3
o	Harden pipeline test result scoping and cleanup 3-4
o	Review PR 5779 (QA Task 35355: Update Automated Test Cases for Change Request 35204) 4-5:15
•	Friday
o	Review PR 5776 (Pull Request 5776: QA Task 35344: Create Automated Test for Bug 32961) 8:15-10
o	Test pipeline fixes 10-12:15, 1:15-4:30
o	PTO (Liam – Nerf War) 4:30-6:30
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
