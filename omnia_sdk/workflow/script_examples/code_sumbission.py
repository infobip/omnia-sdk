import os
import zipfile
from io import BytesIO

import requests

from omnia_sdk.workflow.tools.channels.config import INFOBIP_BASE_URL, INFOBIP_API_KEY

build_workflow_url = f'{INFOBIP_BASE_URL}/workflows/build-workflow'
headers = {"Authorization": f"App {INFOBIP_API_KEY}"}
_manage_workflows_url = f"{INFOBIP_BASE_URL}/workflows/manage"
RESET_POLICY = "RESET"
GRACEFUL_POLICY = "GRACEFUL"


def submit_workflow(directory_path: str, workflow_id: str, session_policy: str = RESET_POLICY) -> None:
    """
    This method submits your code workflow to the Infobip platform.
    Currently, custom dependencies are not supported, so make sure to use only the ones from omnia-sdk.
    In the future, we plan to add support for custom dependencies.

    :param directory_path: path to the root directory with your code workflow
    :param workflow_id: unique id for the workflow, can be resolved from name
    :param session_policy: policy for handling existing sessions after submitting new workflow.
                           RESET: existing sessions are terminated and started on new workflow version.
                           GRACEFUL: existing sessions continue to run on old workflow version for max 25 min,
                           new sessions start on new workflow version.
    """
    zip_buffer = _make_zip_in_memory(directory_path)
    _headers = {'workflow-id': workflow_id, "Authorization": f"App {INFOBIP_API_KEY}", "session-policy": session_policy}
    response = requests.post(build_workflow_url, headers=_headers, files={'workflow_data': zip_buffer})
    print("Status Code:", response.status_code)
    print("Response:", response.text)


def get_workflows() -> list[str]:
    """
    This method retrieves the list of workflows that you have already created.
    :return: List of workflows
    """
    url = f"{_manage_workflows_url}/workflows"
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve workflows:", response.status_code, response.text)
        return []


def _prepare_workflow(workflow_name: str) -> str:
    """
    Returns uuid of existing workflow_name, or creates a new workflow is this is a new name.

    :param workflow_name: Name of the workflow
    """
    workflow_id = get_workflow_id(workflow_name)
    if not workflow_id:
        return create_workflow(workflow_name)
    return workflow_id


def get_workflow_id(workflow_name: str) -> str | None:
    """
    Returns uuid for workflow with the workflow_name, raises ValueError if there is no workflow with this name.
    """
    url = f"{_manage_workflows_url}/workflow"
    response = requests.get(url=url, params={'workflowName': workflow_name}, headers=headers)
    if response.status_code == 200:
        return response.json().get("workflowId")
    else:
        return None


def create_workflow(workflow_name: str) -> str:
    """
    Creates workflow with the given workflow_name, raises ValueError if the name is already used.
    """
    url = f"{_manage_workflows_url}/workflow"
    response = requests.post(url=url, json={'workflowName': workflow_name}, headers=headers)
    if response.status_code == 201:
        return response.json()["workflowId"]
    else:
        raise ValueError(f"Failed to create workflow: {response.status_code}\n{response.text}")


def _rename_workflow(current_name: str, new_name: str):
    url = f"{_manage_workflows_url}/workflow-name"
    workflow_id = get_workflow_id(workflow_name=current_name)
    response = requests.put(url=url, params={'workflowId': workflow_id, 'workflowName': new_name}, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Failed to rename workflow: {response.status_code}\n{response.text}")


def _make_zip_in_memory(dir_path: str) -> BytesIO:
    # creates in-memory .zip archive of the code base
    memory_file = BytesIO()
    base_dir_name = os.path.basename(dir_path.rstrip(os.sep))
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, start=dir_path)
                archive = os.path.join(base_dir_name, rel_path)
                zf.write(full_path, arcname=archive)
    memory_file.seek(0)
    return memory_file


if __name__ == '__main__':
    print(f"existing workflows: {get_workflows()}")
    # gets uuid of existing workflow, or creates new one if this is a new name
    workflow_uuid = _prepare_workflow("<your_workflow_name>")
    submit_workflow(directory_path="<project_root_directory>", workflow_id=workflow_uuid)
    # you should rename the workflow rather than creating a new one to change the name
    # _rename_workflow(workflow_id='<>', new_name='foo')
