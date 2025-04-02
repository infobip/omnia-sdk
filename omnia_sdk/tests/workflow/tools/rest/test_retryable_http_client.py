from unittest.mock import Mock, patch

import pytest
from requests import Response

from omnia_sdk.workflow.tools.rest.exceptions import ApplicationError, UserRequestError
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

test_config = {}
body = b"hello world"
string_body = body.decode("utf-8")


def mock_post_success(**kwargs):
    _ = kwargs
    mock = Mock(spec=Response)
    mock.status_code = 200
    mock.json.return_value = {"response": string_body}
    mock.content = body
    return mock


def mock_post_404(**kwargs):
    _ = kwargs
    mock = Mock(spec=Response)
    mock.status_code = 404
    mock.text = "Not Found"
    return mock


def mock_post_500(**kwargs):
    _ = kwargs
    mock = Mock(spec=Response)
    mock.status_code = 500
    mock.text = "Internal Server Error"
    return mock


def test_success_response():
    response = retryable_request(config={}, x=mock_post_success)
    assert response == {"response": string_body}


def test_success_binary_response():
    response = retryable_request(config={}, x=mock_post_success, decode_json=False)
    assert response == body


@patch("time.sleep", return_value=None)
def test_retries_on_exception_then_succeeds(mock_sleep):
    mock_post = Mock()
    mock_post.side_effect = [Exception("timeout"), mock_post_success()]
    result = retryable_request(config=test_config, x=mock_post)
    assert result == {"response": string_body}
    assert mock_post.call_count == 2
    mock_sleep.assert_called_once()


def test_raises_user_request_error_on_404():
    with pytest.raises(UserRequestError) as exception:
        retryable_request(config=test_config, x=mock_post_404)

    assert exception.value.code == 404
    assert "Not Found" == exception.value.message


@patch("time.sleep", return_value=None)
def test_raises_application_error_after_all_retries(mock_sleep):
    mock_post = Mock()
    mock_post.side_effect = [Exception("timeout"), mock_post_500(), mock_post_500()]

    with pytest.raises(ApplicationError) as exception:
        retryable_request(config=test_config, x=mock_post)

    assert exception.value.code == 500
    assert len(exception.value.trace) == 3
    assert mock_sleep.call_count == 3
