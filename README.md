# Timesheet Helper

Timesheet Helper is a collection of Python scripts designed to process text-based timesheets copied from Microsoft Word. The scripts can remove time spans, calculate the duration of time spans, and format the timesheet for either email or timesheet entry purposes.

## Table of Contents

- [Timesheet Helper](#timesheet-helper)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
  - [Scripts](#scripts)
    - [remove\_times.py](#remove_timespy)
    - [timesheet\_helper.py](#timesheet_helperpy)
    - [timesheet.py](#timesheetpy)
    - [azureDevopsAPI.py](#azuredevopsapipy)
    - [extract\_failed\_tests\_from\_xml.py](#extract_failed_tests_from_xmlpy)
  - [Contributing](#contributing)

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Ensure you have Python installed on your machine. The scripts are written in Python 3.

```bash
# Check Python version
python --version
```

### Installation

Clone the repository to your local machine.

```bash
# Clone the repository
git clone https://github.com/Christopher-C-Robinson/Timesheet_Helper.git
```

## Usage

1. Copy your bulleted timesheet from Microsoft Word.
2. Paste it within the `timesheet.py` script.
3. Run the `timesheet.py` script.

```bash
# Run the script
python timesheet.py
```

## Scripts

### remove_times.py

This script defines a function `remove_timespans` that removes time spans from the text.

### timesheet_helper.py

This script defines a function `replace_with_duration` that replaces time spans in the text with their corresponding durations.

### timesheet.py

This script imports functions from the other two scripts and processes a text-based timesheet.

### azureDevopsAPI.py

This script fetches information about a specific test case from Azure DevOps using the Azure DevOps API.

#### Usage

1. Ensure you have the required environment variables set in a `.env` file:
    - `API_VERSION`
    - `ORGANIZATION`
    - `PERSONAL_ACCESS_TOKEN`

2. Run the script:

```bash
python azureDevopsAPI.py
```

### extract_failed_tests_from_xml.py

This script extracts the names of all failed test cases from multiple XML files and copies the formatted list to the clipboard.

#### Usage

1. Ensure you have the required directories and file paths set in the script.
2. Run the script:

```bash
python extract_failed_tests_from_xml.py
```

## Contributing

If you would like to contribute to the Timesheet Helper project, please feel free to fork the repository, create a feature branch, and submit a pull request.
