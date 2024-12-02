import xml.etree.ElementTree as ET
import pyperclip
import os
import pathlib


def get_xml_files_from_dirs(dirs):
    xml_files = []
    for dir_path in dirs:
        expanded_dir_path = os.path.expanduser(dir_path)
        if not os.path.exists(expanded_dir_path):
            print(f"Directory not found: {expanded_dir_path}")
            continue

        for root, _, files in os.walk(expanded_dir_path):
            for file in files:
                if "report" in file.lower() and file.endswith(".xml"):
                    xml_files.append(os.path.join(root, file))
    return xml_files


# Load the list of XML file paths and directories
dirs = [
    str(pathlib.Path.home() / "Downloads"),
    str(pathlib.Path.home() / "results/reports"),
]
file_paths = get_xml_files_from_dirs(dirs) + [
    # Add additional file paths here as strings
]

# Extract the names of all failed test cases from multiple files
failed_test_cases = []
for file_path in file_paths:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue

    # Skip empty files
    if os.path.getsize(file_path) == 0:
        print(f"Empty file skipped: {file_path}")
        continue

    # Parse the XML file
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError:
        print(f"Parse error in file: {file_path}")
        continue

    # Extract the names of all failed test cases
    for test_case in root.iter("test-case"):
        if test_case.get("result") == "Failed":
            failed_test_cases.append(test_case.get("name"))

# Count the number of failed test cases
num_failed_test_cases = len(failed_test_cases)

# Format the list as requested
formatted_failed_test_cases = "(" + "|".join(failed_test_cases) + ")"

print("Number of failed test cases:\n", num_failed_test_cases)
print("Failed test cases:\n", formatted_failed_test_cases)

# Copy the formatted failed test cases to the clipboard
pyperclip.copy(formatted_failed_test_cases)
