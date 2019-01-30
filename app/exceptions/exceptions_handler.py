import json

from constant import FILE_ERRORS, FILE_ERRORS_DESC, BAD_REQUEST_ERRORS, BAD_REQUEST_ERRORS_DESC, INTERNAL_SERVER_ERROR, \
    INTERNAL_SERVER_ERROR_DESC, INDEX_OUT_OF_BOUND, INDEX_OUT_OF_BOUND_DESC


class CustomClassifierException(Exception):
    def __init__(self, error_code, error_message, status_code, status_message, http_status_code, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.response = {
            "status": {
                "code": "",
                "message": ""
            },
            "errors": []
        }

        self.error = {
            "code": "",
            "message": ""
        }

        self.http_code = http_status_code

        if status_code is not None:
            self.response["status"]["code"] = status_code
        if status_message is not None:
            self.response["status"]["message"] = status_message
        if error_code is not None:
            self.error["code"] = error_code
        if error_message is not None:
            self.error["message"] = error_message
        self.response["errors"].append(self.error)

    # Log Error to database

    def __str__(self):
        return json.dumps(self.response)

    def to_json(self):
        json.dumps(self.response)


class SocketTimeoutException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, *args, **kwargs)


class BlobNotFoundException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, *args, **kwargs)


class BadRequestException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, status_code = BAD_REQUEST_ERRORS, status_message = BAD_REQUEST_ERRORS_DESC, *args, **kwargs)


class UnauthorizedException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, *args, **kwargs)


class InternalServerErrorException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, status_code = INTERNAL_SERVER_ERROR, status_message = INTERNAL_SERVER_ERROR_DESC, http_status_code=INTERNAL_SERVER_ERROR, *args, **kwargs)


class FileNotFoundErrorException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, status_code = FILE_ERRORS, status_message = FILE_ERRORS_DESC , *args, **kwargs)


class HocrParserErrorException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, status_code=INTERNAL_SERVER_ERROR,
                                           status_message=INTERNAL_SERVER_ERROR_DESC, *args, **kwargs)


class IndexOutOfBoundException(CustomClassifierException):
    def __init__(self, *args, **kwargs):
        CustomClassifierException.__init__(self, status_code = INDEX_OUT_OF_BOUND, status_message = INDEX_OUT_OF_BOUND_DESC , *args, **kwargs)

