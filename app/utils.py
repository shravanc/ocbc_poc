import json
import logging
import re
import urllib
from itertools import tee

from config import config
from exceptions.exceptions_handler import BadRequestException, BlobNotFoundException, UnauthorizedException, \
    InternalServerErrorException

from service.table.structures import Line, Point
import cv2 as cv

type_lookup = {
    "unicode": str,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "bool": bool,
    None: type(None),
}


def check_type(obj, typ, message=None):
    """
    Check whether a given object is of the given type. If not, a ValueError is raised.
    :param obj: the object.
    :param typ: the type.
    :param message: The error message.
    :return:
    """
    if isinstance(obj, typ):
        return

    if message is None:
        message = "Expected {} to be of type {}, but got {}".format(obj, typ, type(obj))
    raise ValueError(message)


def check_value(obj, allowed_values, message=None):
    """
    Given an object or a list of objects, checks whether it is in a given list (or set) of allowed_values.
    :param obj: the object (or list of objects).
    :param allowed_values: the list of allowed values.
    :param message: the error message.
    :return:
    """

    # if it's a list, then iterate over the list and check each value
    if type(obj) is list:
        for every_obj in obj:
            check_value(every_obj, allowed_values)
        return

    if obj in allowed_values:
        return

    if message is None:
        message = "Expected to be one of {}, but got {}".format(allowed_values, obj)
    raise ValueError(message)


def get_type_spec(spec):
    if type(spec) not in ["str", "unicode"]:
        return
    if re.match(r"list\[\S+\]", spec):
        return list
    pass


def get_sub_type_spec(spec):
    return re.findall(r"\[\S+\]", spec)[0].lstrip("[").rstrip("]")


def validate_params(params, specification):
    """
    Checks if params follows rule((1.)type of any key's value and (2.)allowed set of values for any key's value)
    :param params: Input Json.
    :param specification: Specification Json.
    :return: None if params is in accordance with specification.

    Eg.
    params = {"image": "http://xyz/something/4.jpg"}
    spec = { "image" : { "type": "str"} }

    """
    logging.debug("Input Json = {}".format(params))
    for key, spec in specification.items():
        logging.info("key = {} and spec = {}".format(key, spec))
        logging.info("is key {} present in input json: {}".format(key, key in params))
        # if the specification doesn't contain 'default', then it is required
        if key not in params:
            if "default" not in spec:
                logging.info("Value Error ")
                raise ValueError("Required param '{}' not specified".format(key))
            else:
                logging.info("Param '{}': Assigning default value '{}'".format(key, spec["default"]))
                params[key] = spec["default"]

        # check allowed
        if "allowed" in spec:
            check_value(params[key], spec["allowed"])
            continue

        # check types
        logging.info("is type included in spec : ".format("type" in spec))
        if "type" in spec:
            if get_type_spec(spec["type"]) == list:
                check_type(params[key], list)
                sub_type = get_sub_type_spec(spec["type"])
                for item in params[key]:
                    check_type(item, type_lookup[sub_type])
            else:
                logging.info("{}'s type in input is {}:".format(key, type(params[key])))
                if type(spec["type"]) is list:
                    logging.debug("spec's type = {}".format(tuple([type_lookup[typ] for typ in spec["type"]])))
                    check_type(params[key], tuple([type_lookup[typ] for typ in spec["type"]]))
                else:
                    check_type(params[key], type_lookup[spec["type"]])


def validate_header(header):
    """
    Validates the request header.
    :param header: Header in dict format.
    :return:
    """
    logging.debug("Validating Headers.")
    if "apikey" not in header:
        logging.error("API key missing in request Header.")
        raise UnauthorizedException(error_code="401 Unauthorized",
                                    error_message="API Key Missing")
    logging.debug("Headers has API key.")

    if header["apikey"] != config["apikey"]:
        logging.error("Invalid API key.", exc_info=True)
        raise UnauthorizedException(error_code="401 Unauthorized",
                                    error_message="Unauthorized API Key")

    logging.debug("Authorized request")


def validate_request(json_template, input_json):
    """
    Validated request data.
    :param json_template: The specification which the request json should be tested against.
    :param input_json: Input request json
    :return:
    """
    try:
        logging.debug("Validating Request.")
        validate_params(input_json, json_template)
    except ValueError as e:
        logging.error("BadRequest Exception", exc_info=True)
        raise BadRequestException(error_code="400 Bad Request",
                                  error_message="Bad Request Body.")


def download_image(image_url, image_path):
    try:
        url_opener = urllib.URLopener()
        url_opener.retrieve(image_url, image_path)
        logging.debug("Image downloaded to {}.".format(image_url))
    except (OSError, IOError) as e:
        logging.error("Disk is full. / {} doesn't exists".format(image_path), exc_info=True)
        raise InternalServerErrorException(error_code="500 Internal Server Error",
                                           error_message=e.message,
                                           status=" Error occured while storing the image as disk is full or"
                                                  " {} does not exists.".format(image_path),
                                           image_id=image_path.split("/")[-1].split(".", -1)[0])

    except Exception as e:
        logging.error("Blob not found. ", exc_info=True)
        raise BlobNotFoundException(error_code="400 Not Found", error_message="blob not found")


def formulate_response(result, status, message):
    """
    Formulates the response of all APIs to one response.
    :param result: list of response.
    :return: formulated response with the wrapper.
    """
    formulated_response = {
        "status": {
            "code": "",
            "message": ""
        },
        "data": {

        },
        "errors": []
    }

    try:
        logging.debug("Result = {}".format(result))

        if result is not None:
            formulated_response["data"] = result

        if status is not None:
            formulated_response["status"]["code"] = status
            formulated_response["status"]["message"] = message
        else:
            formulated_response["status"]["code"] = 500
            formulated_response["status"]["message"] = "Something went wrong."

    except Exception as e:
        logging.error("Internal Server Error while forming response ", exc_info=True)
        raise InternalServerErrorException(error_code=500,
                                           error_message=e.__repr__(),
                                           status_code=500, status_message="Internal Server error occured.")

    return formulated_response


def validate_response(json_template, response, image_path):
    logging.debug("While validaing response. {}".format(response.text))
    try:
        if response.ok:
            # Check for success
            validate_params(json.loads(response.text), json_template["success"])
        elif response.status_code == 500:
            # Check for Internal Server Error Failure
            validate_params(json.loads(response.text), json_template["fail"]["ise"])
        else:
            validate_params(json.loads(response.text), json_template["fail"]["non_ise"])

    except Exception as e:
        logging.error("Internal Server Error while validating response ", exc_info=True)
        raise InternalServerErrorException(error_code="500 Internal Server Error",
                                           error_message=e.message,
                                           status="Error has occured while validating classifiers' response.",
                                           image_id=image_path.split("/")[-1].split(".", -1)[0])


def safe_pad_rect(rect, bg_rect, padding):
    bg_tl_x, bg_tl_y = bg_rect[0]
    bg_br_x, bg_br_y = bg_rect[1]

    rect_tl_x, rect_tl_y = rect[0]
    rect_br_x, rect_br_y = rect[1]

    padded_tl_x = rect_tl_x - padding
    padded_tl_y = rect_tl_y - padding
    padded_br_x = rect_br_x + padding
    padded_br_y = rect_br_y + padding

    if padded_tl_x < bg_tl_x:
        padded_tl_x = bg_tl_x

    if padded_tl_y < bg_tl_y:
        padded_tl_y = bg_tl_y

    if padded_br_x > bg_br_x:
        padded_br_x = bg_br_x

    if padded_br_y > bg_br_y:
        padded_br_y = bg_br_y

    return (padded_tl_x, padded_tl_y), (padded_br_x, padded_br_y)


def safe_pad_line(line, bg_dimension, padding):
    bg_width, bg_height = bg_dimension

    if line.is_horizontal():
        ends_reversed = line.start.x > line.end.x

        x_left, x_right = (line.end.x, line.start.x) if ends_reversed else (line.start.x, line.end.x)

        x_left = x_left - padding
        x_right = x_right + padding

        if x_left < 0:
            x_left = 0

        if x_right > bg_width:
            x_right = bg_width

        start_point, end_point = (Point(x_right, line.start.y), Point(x_left, line.start.y)) if ends_reversed \
            else (Point(x_left, line.end.y), Point(x_right, line.start.y))
        return Line(start=start_point, end=end_point)
    elif line.is_vertical():
        ends_reversed = line.start.y > line.end.y

        y_top, y_bottom = (line.end.y, line.start.y) if ends_reversed else (line.start.y, line.end.y)

        y_top = y_top - padding
        y_bottom = y_bottom + padding

        if y_top < 0:
            y_top = 0

        if y_bottom > bg_height:
            y_bottom = bg_height

        start_point, end_point = (Point(line.start.x, y_bottom), Point(line.start.x, y_top)) if ends_reversed \
            else (Point(line.start.x, y_top), Point(line.start.x, y_bottom))
        return Line(start=start_point, end=end_point)
    else:
        raise ValueError("Can only process horizontal and vertical lines")


def cv_contours_to_lines(contours):
    lines = []
    for contour in contours:
        x, y, width, height = cv.boundingRect(contour)

        if width > height:
            line_y = int((y + (y + height)) / 2)
            lines.append(Line(Point(x, line_y), Point(x + width - 1, line_y)))
        else:
            line_x = int((x + (x + width)) / 2)
            lines.append(Line(Point(line_x, y), Point(line_x, y + height - 1)))
    return lines


def save_images(img_dict):
    """
    Save images in the specified location
    :param img_dict: A dict of the form path->img
    :return: None
    """
    for file_path, img in img_dict.items():
        cv.imwrite(file_path, img)


def is_horizontal_orientation(rotation_angle):
    if rotation_angle == 0 or rotation_angle is None:
        return True
    elif rotation_angle == 90:
        return False

    if rotation_angle % 180 == 0:
        return True

    return False

def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

