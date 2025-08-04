import remove_times
import timesheet_helper

# Place your bulleted timesheet here. The format is based on microsoft word bullets to be copy and pasted in here. You can use the following format:
timesheet = """
•	Monday 
o	Review PR 4897 (Created Test Cases for Data Deletion - Multiple Submissions) 8:15-8:30
o	QA Weekly 8:30-8:45
o	Attempt to do an update via installer 8:45-10:15
o	Review PR 4931 (update conditional builder reference) 10:15-10:30
o	FormsPro 2506.5 Post-Mortem 10:30-12:15
o	Company Meeting 1:30-5
•	Tuesday
o	Engineering/QA Engineering Standup 8:30-8:45
o	Write up task 30761 (Update the `On Prem Server Installation Steps` wiki) 8:45-9
o	[Product/Engineering Hand-Off] Form Submission Dashboard & Data Map Dashboard 9-9:30
o	1on1 w/Mike 9:30-10:30
o	QA defect 30706 (Deep link resubmission shows two FormSubmissions in the network log when processing the offline queue) 10:30-11:15
o	QA defect 30722 (Basic Forms are not added to the pending submission and retried on next sync) 11:15-11:45
o	Review Next pipeline results for the maintenance release 11:45-12, 1-1:45, 2-5:15, 5:45-6:15
o	Write up task 30783 (Data-qa tags broken in the dialog for creating and editing Folders) 1:45-2
o	QA bug 27809 (Popup messages on the Data Connections page in Admin show incorrectly. Prefixed with ServerMessages.) 5:15-5:30
o	QA defect 28676 (The toast message for deleting a data connection `Deleted Successfully.` is not showing when deleting a data connection) 5:30-5:45
•	Wednesday
o	Review PR 4897 (Created Test Cases for Data Deletion - Multiple Submissions) 8:15-8:30, 9-10:15, 10:45-11, 11:15-11:45, 12-1:15, 2:45-3:15
o	Engineering/QA Engineering Standup 8:30-8:45
o	Write up defect 30787 (Toggle cell condition in dynamic table has multiple required asterisks) 8:45-9
o	Write up defect 30792 (Omnitools missing header data in .2 release for IFS data map data connections) 10:15-10:45
o	Write up defect 30793 (Iterator Step Conditional Steps in data maps not saving the condition built) 11-11:15
o	Write up defect 30794 (Data map iterator step for dynamic table has an error in the data map log) 11:45-12
o	Review PR 4902 (Defect Testing/ Test Case Creations for Bugs) 3:15-4:45
o	Review PR 4904 (Created Test Cases for Bug 25833) 4:45-5:15
o	Review PR 4908 (Created Test Case 30744) 5:15-5:30
o	Review PR 4910 (Added Test Cases for Formatted Form descriptions) 5:30-6
o	Review PR 4914 (Created Test cases for condition removal issue in the data maps) 6-6:30
•	Thursday
o	Review Next pipeline results for the maintenance release 8:15-8:30, 8:45-9, 10:30-11, 1:15-6:15
o	Engineering/QA Engineering Standup 8:30-8:45
o	Engineering/Product 9-10
o	Write up defect 30806 (Toggle right align in dynamic table only seems to switch sides with the label but doesn't actually right align) 10-10:30
o	Review PR 4938 (Added tests for NONE option on AUTH) 11-11:15
o	Review PR 4953 (Automation Pipeline Review - Folder Permissions and UI Consistency) 11:15-12
•	Friday
o	Review Next pipeline results for the maintenance release 8:30-12:30, 12:45-2:15
o	QA defect 30399 (Adding Conditions to multiple fields on a Basic Form, causes a save form error for multiple fields with the same reference) 12:30-12:45
"""

print(
    "------------------------------------------------------------------------------------------------------------"
)
print(
    remove_times.remove_timespans(timesheet)
)  # Removes the timespans from the timesheet for email of what you did.
print(
    "------------------------------------------------------------------------------------------------------------"
)
print(
    timesheet_helper.replace_with_duration(timesheet)
)  # Replaces the timespans with the duration of the timespans to be used for timesheet entry.
print(
    "------------------------------------------------------------------------------------------------------------"
)
