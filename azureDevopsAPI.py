import json
import os
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        env_path = Path(".env")
        if not env_path.exists():
            return
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
    else:
        load_dotenv()


def env_value(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


load_dotenv_if_available()

api_version = env_value("AZURE_DEVOPS_API_VERSION", "AZURE_DEVOPS_API_VERSION", default="7.1")
organization = env_value("AZURE_DEVOPS_ORGANIZATION", "AZURE_DEVOPS_ORGANIZATION")
personal_access_token = env_value("AZURE_DEVOPS_PAT")
test_case_id = env_value("AZURE_DEVOPS_TEST_CASE_ID", "TEST_CASE_ID")


def get_test_case_info(
    organization, test_case_id, personal_access_token, api_version="6.0"
):
    """
    Fetches information about a specific test case from Azure DevOps.

    Args:
        organization (str): The name of the organization.
        test_case_id (str): The ID of the test case.
        personal_access_token (str): The personal access token for authentication.
        api_version (str, optional): The API version. Defaults to '6.0'.

    Returns:
        dict: The test case information if the request is successful, otherwise an error message.
    """
    url = f"https://dev.azure.com/{organization}/_apis/testplan/suites?testCaseId={test_case_id}&api-version={api_version}"
    response = requests.get(url, auth=HTTPBasicAuth("", personal_access_token))

    if response.status_code == 200:
        return response.json()
    else:
        return {"Error": response.status_code}


if not organization or not personal_access_token or not test_case_id:
    print(
        "Missing Azure DevOps configuration. Set AZURE_DEVOPS_ORGANIZATION, "
        "AZURE_DEVOPS_TEST_CASE_ID, and AZURE_DEVOPS_PAT in .env.",
        file=sys.stderr,
    )
    raise SystemExit(2)

response = get_test_case_info(
    organization, test_case_id, personal_access_token, api_version
)
print(json.dumps(response, indent=4))
