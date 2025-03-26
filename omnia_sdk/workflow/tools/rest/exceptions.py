class CustomBaseException(Exception):
    """
    Base exception class for all custom exceptions.
    Trace may contain details of all errors which resulted with this exception.

    """

    def __init__(self, code: int, message: str, trace: list = None, *args):
        super().__init__(code, message, trace, *args)
        self.code = code
        self.message = message
        self.trace = trace if trace else []


class ApplicationError(CustomBaseException):
    """
    Exception raised for application errors.
    """

    def __init__(self, code: int, message: str, trace: list = None, *args):
        super().__init__(code, message, trace, *args)


class UserRequestError(CustomBaseException):
    """
    Exception raised for user request errors.
    """

    def __init__(self, code: int, message: str, *args):
        super().__init__(code, message, *args)
