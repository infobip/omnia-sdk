import os
import zipfile
from io import BytesIO

import requests

from omnia_sdk.workflow.tools.channels.config import INFOBIP_BASE_URL, INFOBIP_API_KEY

build_workflow_url = f'{INFOBIP_BASE_URL}/gpt-creator/flow/build-workflow'


def submit_workflow(directory_path: str, workflow_name: str) -> None:
    """
    This method submits your code workflow to the Infobip platform.
    Currently, custom dependencies are not supported, so make sure to use only the ones from omnia-sdk.
    In the future, we plan to add support for custom dependencies.

    :param directory_path: path to the root directory with your code workflow
    :param workflow_name: name of the workflow, reuse the name for same project
    """
    zip_buffer = _make_zip_in_memory(directory_path)
    headers = {'workflow-name': workflow_name, "Authorization": f"App {INFOBIP_API_KEY}"}
    response = requests.post(build_workflow_url, headers=headers, files={'workflow_data': zip_buffer})
    print("Status Code:", response.status_code)
    print("Response:", response.text)


def _make_zip_in_memory(dir_path: str) -> BytesIO:
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
    submit_workflow(directory_path="<your_project>", workflow_name="<your_workflow_name>")
