import requests

from omnia_sdk.workflow.tools.channels.config import INFOBIP_BASE_URL


def synchronous_api():
    content = {"text": "do you offer travel insurance?", "type": "TEXT"}
    json = {"message": content, "workflow_name": "bar", "user_id": "foo"}
    headers = {"session": "A", "chid": "laqo"}

    url = f"{INFOBIP_BASE_URL}/gpt-creator/flow/inbound-api"
    resp = requests.post(url, json=json, headers=headers)
    print(resp.json())


if __name__ == '__main__':
    synchronous_api()
