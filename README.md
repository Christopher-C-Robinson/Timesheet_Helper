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

### GitHub Pages (Recommended - No Installation Required)

Visit the live application at: **https://christopher-c-robinson.github.io/Timesheet_Helper/**

1. Paste your bulleted timesheet from Microsoft Word into the text area
2. Click "Process Timesheet" to get both email format and duration format outputs

### Local Flask Development

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the web application:
```bash
python app.py
```

3. Open your browser and go to `http://localhost:5000`
4. Paste your bulleted timesheet from Microsoft Word into the text area
5. Click "Process Timesheet" to get both email format and duration format outputs

### Generating Static Site for GitHub Pages

To regenerate the static site files:

```bash
python freeze.py
```

This will create/update the `docs/` directory with static HTML files that can be deployed to GitHub Pages.

### Command Line Interface

1. Copy your bulleted timesheet from Microsoft Word.
2. Paste it within the `timesheet.py` script.
3. Run the `timesheet.py` script.

```bash
# Run the script
python timesheet.py
```

## Scripts

### app.py

This script provides a web interface for the Timesheet Helper. It uses Flask to create a simple web application where users can paste their timesheet data and get both email and duration formats as output.

### freeze.py

This script converts the Flask application to static HTML files suitable for GitHub Pages deployment. It uses Frozen-Flask to generate static files in the `docs/` directory that preserve all the original functionality using client-side JavaScript.

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

## GitHub Pages Deployment

This project is configured for automatic deployment to GitHub Pages. The static site is generated in the `docs/` directory and served directly from GitHub Pages.

### Automatic Deployment

The repository is configured to serve the static site from the `docs/` directory. Any changes pushed to the main branch will automatically update the live site at:
**https://christopher-c-robinson.github.io/Timesheet_Helper/**

### Manual Regeneration

To manually regenerate the static site files:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the freeze script:
```bash
python freeze.py
```

3. Commit and push the updated `docs/` directory:
```bash
git add docs/
git commit -m "Update static site"
git push
```

### Local Testing

To test the static site locally:

```bash
cd docs
python -m http.server 8000
```

Then visit `http://localhost:8000` in your browser.

## Converting from Flask to Static Site

The conversion process involved:

1. **Adding Frozen-Flask**: Used to generate static HTML files from Flask routes
2. **JavaScript Conversion**: Ported Python timesheet processing logic to client-side JavaScript
3. **Static Template**: Created a standalone HTML file with embedded CSS and JavaScript
4. **Build Process**: Implemented `freeze.py` script to generate the static site

All original functionality is preserved in the static version, including:
- Timesheet text processing
- Email format generation (removes time spans)
- Duration format generation (calculates hours worked)
- Weekly total calculations

## Contributing

If you would like to contribute to the Timesheet Helper project, please feel free to fork the repository, create a feature branch, and submit a pull request.
