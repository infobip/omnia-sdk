# Omnia-sdk

This SDK lets user build LangGraph applications bundled with Infobip's AI, CPaaS and SaaS platforms.
Solutions built with the SDK can be deployed to our platform for distributed session management, high availability and
scalability.

# Infrastructure

You could consider platform as distributed stateful inference server for automated (AI) workflows.

Workflows built with this SDK can be deployed in Infobip's platform which will ensure that the workflow is highly
available and scalable.
Platform will also ensure additional features such as automatic language detection and localization with synchronous and
asynchronous endpoints to the workflow.

# Code submission

Code can be deployed using the:

- code_submission.py module
  There is a rest endpoint example which accepts .zip file with the code and deploys it to the platform.

Expected files in the zip file:

- project directory with source code and yaml files
- chatbot_configuration.yaml (mandatory)
- translation_table.yaml (optional)
- build.yaml (optional)

2 options are supported right now, we will make it more flexible in the future.

#### With python package root

- package_root_directory:
    - graph.py
    - chatbot_configuration.yaml
    - translation_table.yaml
    - build.yaml
    - other_python_packages

#### With project directory

- project_directory:
    - package_root_directory:
        - graph.py
        - chatbot_configuration.yaml
        - translation_table.yaml
        - build.yaml
        - other_python_packages

##### Custom dependencies

Currently custom dependencies are not supported, please use those available in the SDK.

## How to use

We first recommended that user checks the TinyChatbot example in the `examples` directory.
The example demonstrates how to build a simple chatbot that can be deployed in Infobip's platform.
From there, user may check more complex examples here:

- https://github.com/infobip/omnia-sdk-examples

Afterward, looking at the source code and documentation of ChatbotFlow class is recommended to get full understanding of
the SDK.

Workflows are 100% runnable in local environment, user only needs to set Infobip's API key in the environment variable
`INFOBIP_API_KEY`.

## Installation

To install the SDK for local development we recommend poetry environment:

- poetry add git+https://github.com/infobip/omnia-sdk.git

Python 3.12.X or 3.13.X is mandatory.

Client should expect that Infobip's endpoints are always available and that the SDK will handle all the necessary
retries and error handling.

## Sender registration

For now sender can be registered via build.yaml file.
We should soon enable registration via the API outside code submission, and automatic callback registration for the
sender/channel combinations.

## Production inference

Built workflows will receive traffic via Infobip's OmniChannel API from all supported channels
Additionally, there are two HTTP endpoints that can be used to send messages to the workflow:

- /gpt-creator/flow/inbound-api
- /gpt-creator/flow/inbound-api-callback

check the omnia_sdk/examples/http_api_example.py for more details.

note: these urls are temporary and will be changed in the future

## Logs

You can access workflow logs via REST endpoints. Check example in get_logs.py.
You should be able to use logging via standard logging idiom in python:

```python
import logging as log
```
or
```python
import logging
```
Workflow server will ensure that logging is properly configured when you submit the workflow.