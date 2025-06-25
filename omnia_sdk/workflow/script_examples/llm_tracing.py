import requests

from omnia_sdk.workflow.script_examples.code_sumbission import get_workflows, get_workflows_versions
from omnia_sdk.workflow.tools.channels.config import INFOBIP_BASE_URL, INFOBIP_API_KEY

headers = {"Authorization": f"App {INFOBIP_API_KEY}"}
ai_reporting_url = f'{INFOBIP_BASE_URL}/ai-reporting'


def get_workflows_sessions(workflow_id: str = None, workflow_version: str = None, from_timestamp: str = None,
                           to_timestamp: str = None) -> list[str]:
    """
    Retrieves sessions of a specific workflow or all workflows if no parameters are provided. If time range is provided,
    we return sessions that had interactions within that range.

    :param workflow_id: unique identifier of workflow
    :param workflow_version: version of specific workflow
    :param from_timestamp: start time in ISO  format (e.g. "2025-01-01T00:00:00")
    :param to_timestamp: end time in ISO format
    :return: List of workflow sessions
    """
    url = f"{ai_reporting_url}/model-proxy-sessions"
    response = requests.get(url=url, params={
        'workflowId': workflow_id, "workflowVersion": workflow_version, "from": from_timestamp, "to": to_timestamp
        }, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve workflows sessions:", response.status_code, response.text)
        return []


def get_session_tracing(session_id: str) -> list[dict]:
    """
    Retrieves llm tracing information for a specific session by its session ID.

    :param session_id: unique identifier of the session
    :return: List of tracing information for the session
    """
    url = f"{ai_reporting_url}/model-proxy-sessions/{session_id}"
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve session tracing:", response.status_code, response.text)
        return []


if __name__ == '__main__':
    print(f"Existing workflows: {get_workflows()}")

    # outputs all workflow versions
    # print(get_workflows_versions(workflow_id=<workflow_id>))

    # Get all sessions for a specific workflow id and version
    # print(get_workflows_sessions(workflow_id=<workflow_id>, workflow_version=<workflow_version>))

    # Get session tracing for a specific session id
    # print(get_session_tracing(session_id=<session_id>))
