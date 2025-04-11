# Omnia-sdk

This SDK lets user build LangGraph applications bundled with Infobip's AI, CPaaS and SaaS platforms.

# Infrastructure
Workflows built with this SDK can be deployed in Infobip's platform which will ensure that the workflow is highly available and scalable.
Platform will also ensure additional features such as automatic language detection and localization with synchronous and asynchronous endpoints to the workflow.
You could consider platform as a distributed stateful inference server for automated (AI) workflows.

# Code submission
TODO

## How to use
We first recommended that user checks the TinyChatbot example in the `examples` directory.
The example demonstrates how to build a simple chatbot that can be deployed in Infobip's platform.
From there, user may check more complex examples here:
 - https://github.com/infobip/omnia-sdk-examples

Afterward, looking at the source code and documentation of ChatbotFlow class is recommended to get full understanding of the SDK.

Workflows are 100% runnable in local environment, user only needs to set Infobip's API key in the environment variable `INFOBIP_API_KEY`.

## Installation
To install the SDK for local development we recommend poetry environment:
 - poetry add git+https://github.com/infobip/omnia-sdk.git

Python 3.12.X or 3.13.X is mandatory.

Client should expect that Infobip's endpoints are always available and that the SDK will handle all the necessary retries and error handling.