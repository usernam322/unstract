from prompt_studio.prompt_studio_core.constants import ToolStudioErrors
from rest_framework.exceptions import APIException


class PlatformServiceError(APIException):
    status_code = 400
    default_detail = ToolStudioErrors.PLATFORM_ERROR


class ToolNotValid(APIException):
    status_code = 400
    default_detail = "Custom tool is not valid."


class PromptNotValid(APIException):
    status_code = 400
    default_detail = "Input prompt instance is not valid.\
          Seems it is either empty or no prompt is mapped."


class IndexingError(APIException):
    status_code = 400
    default_detail = "Error while indexing file"


class AnswerFetchError(APIException):
    status_code = 500
    default_detail = "Error occured while fetching response for the prompt"


class DefaultProfileError(APIException):
    status_code = 400
    default_detail = "Default profile is not selected. \
        Please select one from Profile manager."


class EnvRequired(APIException):
    status_code = 404
    default_detail = "Environment variable not set"


class OutputSaveError(APIException):
    status_code = 500
    default_detail = "Unable to store the output."


class ToolDeleteError(APIException):
    status_code = 500
    default_detail = "Failed to delete the error"