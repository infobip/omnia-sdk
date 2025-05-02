import requests

from omnia_sdk.workflow.script_examples.code_sumbission import get_workflows, get_workflow_id
from omnia_sdk.workflow.tools.channels.config import INFOBIP_API_KEY

url = "https://api-ny2.infobip.com/workflows/manage/workflow-channel"
headers = {"Authorization": f"App {INFOBIP_API_KEY}"}


def register_channel_for_workflow(workflow_id: str, channel_id: str, channel: str):
    """
    Routes traffic to workflow for a specific channel.

    :param workflow_id: Id of the workflow
    :param channel_id: Id of the channel, msisdn for WhatsApp...
    :param channel: Type of the channel, e.g. WHATSAPP
    """
    resp = requests.post(url=url, json={"channel": channel, "channelIdentity": channel_id, "workflowId": workflow_id}, headers=headers)
    print(resp.status_code)
    print(resp.json())


def delete_channel_for_workflow(workflow_id: str, channel_id: str, channel: str, use_conversations: bool = False):
    """
    Deletes the channel from workflow and stops routing traffic to it. Traffic will be routed back to Conversations.
    :param workflow_id: Id of the workflow
    :param channel_id: Id of the channel, msisdn for WhatsApp...
    :param channel: Type of the channel, e.g. WHATSAPP
    :param use_conversations: If True, traffic will be routed back to Conversations. If False, traffic will be routed back to previous SaaS endpoint.
    If channel_id is configured with Answers chatbot WITHOUT Conversations, use False always.
    """
    params = {"channel": channel, "channelIdentity": channel_id, "workflowId": workflow_id, "useConversations": use_conversations}
    resp = requests.delete(url=url, params=params, headers=headers)
    print(resp.status_code)


def get_workflow_channels():
    """
    Lists all channels that are registered for a specific workflow.
    """
    resp = requests.get(url=f'{url}s', headers=headers)
    print(resp.status_code)
    print(resp.json())
    return resp.json()


if __name__ == '__main__':
    print(get_workflow_channels())
    print(get_workflows())
    #workflow_uuid = get_workflow_id(workflow_name="insurance_demo")
    #register_channel_for_workflow(workflow_id=workflow_uuid, channel_id="<MSISDN>", channel="WHATSAPP")
    #delete_channel_for_workflow(workflow_id=workflow_uuid, channel_id="<MSISDN>", channel="WHATSAPP")
