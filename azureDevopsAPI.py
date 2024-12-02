import json
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

test_case_id = 12345
# Load environment variables from .env file
load_dotenv()

api_version = os.getenv("AZURE_DEVOPS_API_VERSION")
organization = os.getenv("AZURE_DEVOPS_ORGANIZATION")
personal_access_token = os.getenv("AZURE_DEVOPS_PAT")


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


response = get_test_case_info(
    organization, test_case_id, personal_access_token, api_version
)
print(json.dumps(response, indent=4))
