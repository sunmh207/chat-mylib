class BaseException(Exception):
    def __init__(self, message):
        self.message = message


class ExceededMaxPagesError(BaseException):
    def __init__(self, message):
        self.message = message


class ExceededMaxWordsError(BaseException):
    def __init__(self, message):
        self.message = message


class UnsupportedError(BaseException):
    def __init__(self, message):
        self.message = message
