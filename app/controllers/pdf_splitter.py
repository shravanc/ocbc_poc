import logging
import time

from flask import request
from flask_restful import Resource

from exceptions.exceptions_handler import *
from service.pdf_split_service import PDFSplitService
from utils import formulate_response


class SplitPDF(Resource):

    def post(self):
        try:
            start_time = time.time()
            req_payload = request.get_json()
            file_location = req_payload['pdf_doc_location']
            page_folder_location = req_payload['page_dir_location']
            pdf_split_service = PDFSplitService()
            result = pdf_split_service.split_pdf(file_location, page_folder_location)
            logging.info("%s seconds" % (time.time() - start_time))
            return formulate_response(result, 200, "Success")

        except CustomClassifierException as e:
            logging.error("Error {} has occured in controller".format(e))
            return e.response, e.http_code

        except Exception as e:
            logging.error("Error in service = {}".format(e), exc_info=True)
            return InternalServerErrorException(error_code=500,
                                                error_message="PDF couldn't be splitted").response, 500
        finally:
            logging.info("API Call Finished Successfully")
