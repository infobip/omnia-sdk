import requests

from omnia_sdk.workflow.script_examples.code_sumbission import get_workflow_id
from omnia_sdk.workflow.tools.channels.config import INFOBIP_BASE_URL, INFOBIP_API_KEY


def synchronous_api(workflow_name: str = "insurance_demo"):
    # assumes there is built workflow with name "example-workflow"
    workflow_id = get_workflow_id(workflow_name=workflow_name)
    content = {"text": "do you offer travel insurance?", "type": "TEXT"}
    json = {"message": content, "workflow_id": workflow_id, "user_id": "user1"}
    headers = {"session": "B", "Authorization": f"App {INFOBIP_API_KEY}"}
    url = f"{INFOBIP_BASE_URL}/workflows/inbound-api"
    resp = requests.post(url, json=json, headers=headers)
    print(resp.json())


if __name__ == '__main__':
    synchronous_api()
