import os
from enum import Enum

# AWS_INSTANCE_IP = "http://54.190.155.131:9999"
AWS_INSTANCE_IP = "http://54.245.29.69:6789"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


DE_APPLICATION_NAME = "morning_star_data_extraction"
PDF_QUALITY_APPLICATION_NAME = "pdf_quality"
SPLIT_PDF_APPLICATION_NAME = "split_pdf"

""" Constants module which defines all status/error code
    and messages at global level
"""

FILE_ERRORS = 404
FILE_ERRORS_DESC = "File Not Found Error"

BAD_REQUEST_ERRORS = 400
BAD_REQUEST_ERRORS_DESC = "Bad Request Error"

INTERNAL_ERVER_ERROR = 500
INTERNAL_ERVER_ERROR_DESC = "Internal Server Error"

INDEX_OUT_OF_BOUND = 6001
INDEX_OUT_OF_BOUND_DESC = "Index out of Bound Error."

INTERNAL_SERVER_ERROR = 500
INTERNAL_SERVER_ERROR_DESC = "Internal Server Error Occurred."

ERR_FILE_READ = 4001
ERR_FILE_READ_DESC = "File not found"

ERR_FILE_WRITE = 4002
ERR_FILE_WRITE_DESC = "File couldn't be saved"

ERR_PANEL_HEADER_EXTRACTION = 1003
ERR_PANEL_HEADER_EXTRACTION_DESC = "Failed to extract panel header"

ERR_PANEL_BODY_EXTRACTION = 1004
ERR_PANEL_BODY_EXTRACTION_DESC = "Failed to extract panel body"

ERR_HOCR_WORD_JSON_CONVERSION = 1005
ERR_HOCR_WORD_JSON_CONVERSION_DESC = "Failed to convert hocr to word json"

ERR_BAD_REQUEST = 5001
ERR_BAD_REQUEST_DESC = "Mandatory Fields weren't present."

ERR_BAD_REQUEST_DOC_TYPE = 5002
ERR_BAD_REQUEST_DOC_TYPE_DESC = "Invalid document type"

ERR_HOCR_PARSER = 5003
ERR_HOCR_PARSER_DESC = "Error while parsing the hocr string"

"""
    PDF Split Constants
"""

RESPONSE_TEMPLATE_JSON = "response_template.json"
EXTRACTED_WORD_JSON = "extracted_word.json"

# PORT_NUMBER = 8090
PORT_NUMBER = 6789
PDF_QUALITY_PORT_NUMBER = 2222
SPLIT_PDF_PORT_NUMBER = 1111
HOST = "0.0.0.0"
PDF_UPLOAD_DIRECTORY = os.path.join(PROJECT_ROOT, "uploads")

APP_ROOT = os.path.dirname(os.path.abspath(__file__))  # refers to application_top
APP_MODEL = os.path.join(APP_ROOT, 'models')  # refers to application_models
APP_CONTROLLER = os.path.join(APP_ROOT, 'controllers')  # refers to application_controllers
APP_RESOURCE = os.path.join(APP_ROOT, 'resources')  # refers to the files used for testing

"""
    Machined vs Scanned Constants
"""
THRESHOLD_FOR_SCANNED_PDF = 10

"""
    Header Meta Info Constants
"""

HEADER_TAB_SPACE_PIXELS = 25
HEADER_LINE_VERTICAL_PIXELS = 8

"""ENUMS"""


class DocType(Enum):
    SCANNED = "scanned"
    MACHINED = "machined"


"""PDF Quality Constants"""

GOOD_PDF_QUALITY = 90
GOOD_PDF_QUALITY_THRESHOLD = 3500
PDF_QUALITY_RATIO = 40

"""ParseMethod= abby/opencv"""
DEFAULT_PARSE_METHOD = 'opencv'