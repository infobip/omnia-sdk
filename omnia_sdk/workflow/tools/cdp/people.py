import requests

from omnia_sdk.workflow.tools.channels.config import INFOBIP_API_KEY, INFOBIP_BASE_URL
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

headers = {
    "Content-Type": "application/json",
    "Authorization": f"App {INFOBIP_API_KEY}",
    "Cookie": "IbEntryLocale=en-US",
}

"""
This module provides integration with Infobip People service. People service is used to store and manage customer profiles.
Currently supported methods allow users to fetch People data for single user or multiple users.

If any of the method fails after retry attempts, ApplicationError is raised.
Often user may proceed without information from People service, so it is up to the user to decide how to handle the error.
"""


def get_people_profile(identifier: str, id_type: str, config: dict, sender: str = None) -> dict:
    """
    Returns profile for person identified by the identifier.
    More details: https://www.infobip.com/docs/api/customer-engagement/people/get-a-single-person-or-a-list-of-people

    :param identifier: unique identifier
    :param id_type: phone, WhatsApp, email, etc. as in docs above
    :param config: session and channel details
    :param sender: sender ID
    @return: profile of the person, ApplicationError is raised if People service is not available
    """
    data = {
        "type": id_type,
        "identifier": identifier,
    }
    if sender:
        data["sender"] = sender
    response_json = retryable_request(
        config, requests.post, url=f"{INFOBIP_BASE_URL}/people/2/custom/persons/find", headers=headers, json=data
    )
    return response_json


def get_people_profiles(config: dict, **kwargs) -> dict:
    """
    Returns profile for persons identified by the filter in **kwargs.
    More details: https://www.infobip.com/docs/api/customer-engagement/people/get-a-single-person-or-a-list-of-people
    Filter should be sent as dict.

    :param config: session and channel details
    :param kwargs: filter parameters
    @return: profiles of the people, ApplicationError is raised if People service is not available
    """
    response_json = retryable_request(
        config, requests.post, url=f"{INFOBIP_BASE_URL}/people/2/custom/persons/find/list", headers=headers, body=kwargs
    )
    return response_json


def create_person_profile(data: dict, config: dict) -> None:
    """
    Creates a new person profile.
    More details: https://www.infobip.com/docs/api/customer-engagement/people/create-a-new-person

    :param data: person data, see API docs above
    :param config: session and channel details
    @return: profile of the person, ApplicationError is raised if People service is not available
    """
    retryable_request(config, requests.post, url=f"{INFOBIP_BASE_URL}/people/2/persons", headers=headers, json=data)


def update_person_profile(identifier: str, id_type: str, sender: str, data: dict, config: dict) -> None:
    """
    Updates a person profile.
    More details: https://www.infobip.com/docs/api/customer-engagement/people/update-a-person

    :param sender: sender or application id
    :param identifier: unique identifier
    :param id_type: phone, WhatsApp, email, etc. as in docs above
    :param data: person data
    :param config: session and channel details
    """

    params = {
        "identifier": identifier,
        "type": id_type,
        "sender": sender,
    }
    retryable_request(config, requests.put, url=f"{INFOBIP_BASE_URL}/people/2/persons/", headers=headers, json=data, params=params)


def delete_person(config: dict, identifier: str, sender: str, id_type: str) -> None:
    """
    Deletes a person profile.
    More details: https://www.infobip.com/docs/api/customer-engagement/people/delete-a-person
    :param config: session and channel details
    :param identifier: unique user identifier
    :param sender: sender or application id
    :param id_type: phone, WhatsApp, email, etc. as in docs above
    """
    params = {
        "identifier": identifier,
        "type": id_type,
        "sender": sender,
    }
    retryable_request(config, requests.delete, url=f"{INFOBIP_BASE_URL}/people/2/persons/", headers=headers, params=params)
