import os

import requests

from omnia_sdk.workflow.script_examples.code_sumbission import get_workflow_id
from omnia_sdk.workflow.tools.channels.config import INFOBIP_BASE_URL, INFOBIP_API_KEY
logs_url = f'{INFOBIP_BASE_URL}/workflows'


def get_logs(workflow_name: str, download_dir: str = "./") -> None:
    url = f"{logs_url}/logs"
    filename = f"{workflow_name}_logs.zip"
    workflow_id = get_workflow_id(workflow_name=workflow_name)
    headers = {'workflow-id': workflow_id, "Authorization": f"App {INFOBIP_API_KEY}"}
    _download(url=url, headers=headers, download_dir=download_dir, filename=filename)

def get_app_error_logs(download_dir: str= "./") -> None:
    url = f"{logs_url}/app-error-logs"
    headers = {"Authorization": f"App {INFOBIP_API_KEY}"}
    filename = "app_error_logs.zip"
    _download(url=url, headers=headers, download_dir=download_dir, filename=filename)

def _download(url: str, headers: dict, download_dir: str, filename: str) -> None:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(os.path.join(download_dir, filename), "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved ZIP file as {filename}")
    else:
        print("Failed to download error logs:", response.status_code, response.text)



if __name__ == "__main__":
    get_logs(workflow_name ="<workflow_name>")
    get_app_error_logs()
