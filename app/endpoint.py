import json
import logging
import pathlib
import uuid
from decimal import Decimal
from os import path

from flask import Flask, request
from flask import jsonify
from flask import send_from_directory
from flask_cors import CORS
from flask_restful import Api
from healthcheck import HealthCheck

import constant
from constant import DE_APPLICATION_NAME
from controllers.extract_data import extract_translated_data
from exceptions.exception_logger import create_logger
from log import configure_logger, DE_LOG_FILE_PATH




class DataExtractorJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return json.JSONEncoder.default(self, o)


class DEConfig:
    RESTFUL_JSON = {"cls": DataExtractorJSONEncoder}


de_health = HealthCheck()

app = Flask(DE_APPLICATION_NAME)
configure_logger(app.logger, logging.INFO, DE_LOG_FILE_PATH)
create_logger(DE_LOG_FILE_PATH)
app.config.from_object(DEConfig)
CORS(app)

api = Api(app, catch_all_404s=True)



# Extract data API for Machines and Scanned PDF.
# api.add_resource(ExtractData, "/extract/data")

# Flask route to expose Health Check information
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: de_health.run())


# @app.before_request
# def log_request():
#     app.logger.info("Request:\n{}".format(request.get_json()))
#
#
# @app.after_request
# def log_response(response):
#     app.logger.info("Response:\n{}".format(response.data.decode()))
#     return response


@app.route('/<string:pdf>/html/<string:page>', methods=["GET"])
def access_pdf(pdf, page):
    directory = "uploads/" + pdf + '/html/'
    resp = send_from_directory(directory, page)
    return resp
    
@app.route('/', methods=["GET"])
def home_page_route():
    resp = send_from_directory("static", "index.html")
    return resp

@app.route('/test', methods=['GET'])
def home():
    resp = send_from_directory("static", "start.html")
    return resp


@app.route('/extract', methods=["POST"])
def extract_data_route():
    try:
        pathlib.Path(constant.PDF_UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
        req_dict = parse_extract_data_request()

        file = req_dict["file"]
        file_name = request.files["file"].filename.replace(' ', '_')
        file_name_without_ext = path.splitext(file_name)[0]
        uuid_filename = file_name_without_ext + "_" + str(uuid.uuid1())
        file_location = path.join(constant.PDF_UPLOAD_DIRECTORY, f"{uuid_filename}.pdf")
        file.save(file_location)
        prediction, check_box = extract_translated_data(uuid_filename, file_location, req_dict['start_page'], req_dict['end_page'], req_dict['lang'])

        print("--->prediction--->", prediction)
        pred = prediction.to_json()
        for d in check_box.required_data:
            pred[d['field']] = d['text']
        return jsonify({'data': pred})
        # return jsonify(check_box.response)
        # return jsonify(prediction.to_json())
        # return success_response(extract_data)
    except Exception as e:
        return error_response(str(e))



def success_response(data):
    resp = {
        "data": data
    }
    return jsonify(resp)


def error_response(msg):
    resp = {
        "error": msg
    }

    return jsonify(resp)


def parse_extract_data_request() -> dict:
    # if 'file' not in request.files:
    #     raise AssertionError("Property `file` not found in multipart")
    #
    # if 'start_page' not in request.form:
    #     raise AssertionError("Mandatory property `start_page` needed")
    #
    # if 'end_page' not in request.form:
    #     raise AssertionError("Mandatory property `end_page` needed")
    #
    # if 'lang' not in request.form:
    #     raise AssertionError("Mandatory property `lang` needed")

    return {
        'file': request.files['file'],
        'start_page': 1, #request.form["start_page"],
        'end_page': 1, #request.form["end_page"],
        'lang': 'en' #request.form["lang"]
    }


if __name__ == "__main__":
    app.run(debug=True, host=constant.HOST, port=constant.PORT_NUMBER)
