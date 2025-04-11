import requests

from omnia_sdk.workflow.tools.channels.config import INFOBIP_BASE_URL, INFOBIP_API_KEY


def synchronous_api():
    # assumes there is built workflow with name "example-workflow"
    content = {"text": "do you offer travel insurance?", "type": "TEXT"}
    json = {"message": content, "workflow_name": "example-workflow-2", "user_id": "user1"}
    headers = {"session": "B", "Authorization": f"App {INFOBIP_API_KEY}"}
    url = f"{INFOBIP_BASE_URL}/gpt-creator/flow/inbound-api"
    resp = requests.post(url, json=json, headers=headers)
    print(resp.json())

if __name__ == '__main__':
    synchronous_api()
