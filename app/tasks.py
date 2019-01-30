from celery import Celery
from celery import group
from flask import Flask, request
from constant import DE_APPLICATION_NAME
import json
from flask_cors import CORS


#####
import logging
import re
import subprocess

import six
from google.cloud import translate

from constant import ERR_FILE_READ, ERR_FILE_READ_DESC
from exceptions.exceptions_handler import *
from log import timeit
from service.preeti_font_converter import convert
from utils import formulate_response
#####



class DataExtractorJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return json.JSONEncoder.default(self, o)


class DEConfig:
    RESTFUL_JSON = {"cls": DataExtractorJSONEncoder}


app = Flask(DE_APPLICATION_NAME)
app.config.from_object(DEConfig)
CORS(app)


# Intialize Celery
celery = Celery('endpoint', backend='rpc://', broker='amqp://infrrd:infrrd123@localhost/infrrd_vhost')
celery.conf.update(app.config)


#############

def translate_text(text, lang):
    print("***********TRANSLATE_TEXT************", text, lang )
    # [START translate_translate_text]
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """

    translate_client = translate.Client()

    print("---TRANS_1---")
    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    print("---TRANS_2---")
    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(
        text, source_language=lang, target_language='en')
    
    return result['translatedText']


# @timeit
# @celery.task
def extract_cell_data(pdf_path, pdf_text_cmd, lang, cordinates, gv):
    print("----1111----", gv, cordinates)
    try:
        
        pdf_text_process = subprocess.Popen(pdf_text_cmd, shell=True, stdout=subprocess.PIPE)
        text = pdf_text_process.communicate()[0]
        # print("1*****EXTRACT_CELL_DATA*****", text)
        text = text.replace(b'\x0c', b'')
        # print("2*****EXTRACT_CELL_DATA*****")

        if 'LEE' in str(text):
            print("2**************TEXT***************")
            print(pdf_text_cmd)
            print(text)
            print(cordinates)
            print("2**************TEXT***************")

        logging.info(u'Actual Text: {}'.format(text))
        if lang == "en":
            vision_text = gv.test(cordinates['x'], cordinates['y'], cordinates['h'], cordinates['w'])
            print("VISION_TEXT====>>", vision_text)
            return vision_text #text.decode('utf-8')
            # return text.decode('utf-8')
        char_count = len(re.findall(r"[a-zA_Z]", text.decode("utf-8")))
        digit_matches = re.findall(r"\d", text.replace(b',', b'').decode("utf-8"))
        if len(digit_matches) > int(char_count * 0.50):
            translated_text = text.decode("utf-8")
            translated_text = translated_text.replace('?=', 'Rs')
            translated_text = translated_text.replace('cf=j=', 'I.')
        else:
            text_list = text.decode().split('\n')
            translated_text = ''
            for text_data in text_list:
                if lang == 'ne':
                    text_data = convert(text_data)
                translated_text = translated_text + translate_text(text_data, lang) + "\n"
                translated_text = translated_text.replace('&quot;', '"')
                translated_text = translated_text.replace('&#39;', '\'')
                translated_text = translated_text.replace('?=', 'Rs')
                translated_text = translated_text.replace('cf=j=', 'I.')

        if pdf_text_process.returncode != 0:
            return formulate_response("Failed for atleast one pdf page", 500, "Failed")
        return translated_text

    except FileNotFoundError as e:
        print("1--ERROR-->", e)
        logging.error("File Not Found Error {} has occured in controller".format(e), exc_info=True)
        raise FileNotFoundErrorException(error_code=ERR_FILE_READ,
                                         error_message=ERR_FILE_READ_DESC,
                                         http_status_code=INTERNAL_SERVER_ERROR)

    except IndexError as e:
        print("2--ERROR-->", e)
        logging.error("Index Bound Error {} has occured in controller".format(e), exc_info=True)
        raise IndexOutOfBoundException(error_code=INDEX_OUT_OF_BOUND, error_message=INDEX_OUT_OF_BOUND_DESC,
                                       http_status_code=INTERNAL_SERVER_ERROR)

    except Exception as e:
        print("3--ERROR-->", e)
        logging.error("Error in service = {}".format(e), exc_info=True)
        raise InternalServerErrorException(error_code=INTERNAL_SERVER_ERROR,
                                           error_message="Couldn't read pdf.")


# @celery.task
def pdf_page_to_image_task(file_path,
                      output_file_path,
                      dpi=300,
                      jpeg_compression_quality=100, ):
    """
    Given a single page pdf's `file_path` convert it to a jpg file of `dpi` resolution and save it as
    `output_file_path`.
    :param file_path: File path of the input pdf
    :param output_file_path: File path where the resultant image should be stored
    :param jpeg_compression_quality: An integer in [1, 100]
    :param dpi: resolution of the resultant image
    """

    print("*****************PDF_PAGE_TO_IMAGE_TASK******************")
    args = [
        "gs",
        "-dNOPAUSE",
        "-dBATCH",
        "-dSAFER",
        "-sDEVICE=jpeg",
        f"-dJPEGQ={jpeg_compression_quality}",
        f"-r{dpi}",
        f"-sPageList={1}",
        "-dQUIET",
        f"-sOutputFile={output_file_path}",
        file_path
    ]

    print("----ARGS---->", args)
    subprocess.check_output(args)



def pdf_page_to_regular_image_task(file_path,
                      output_file_path,
                      dpi=300,
                      jpeg_compression_quality=100, ):
    """
    Given a single page pdf's `file_path` convert it to a jpg file of `dpi` resolution and save it as
    `output_file_path`.
    :param file_path: File path of the input pdf
    :param output_file_path: File path where the resultant image should be stored
    :param jpeg_compression_quality: An integer in [1, 100]
    :param dpi: resolution of the resultant image
    """

    print("*****************PDF_PAGE_TO_IMAGE_TASK******************")
    args = [
        "gs",
        "-dNOPAUSE",
        "-dBATCH",
        "-dSAFER",
        "-sDEVICE=jpeg",
        f"-sPageList={1}",
        "-dQUIET",
        f"-sOutputFile={output_file_path}",
        file_path
    ]

    print("----ARGS---->", args)
    subprocess.check_output(args)


# pdf_page_to_image_task('/Users/shravanc/flask/flask_apps/ocbc/app/uploads/5_4f713c0e-22ce-11e9-841e-1c36bb1a4426/pages/page-1.pdf', '/Users/shravanc/flask/flask_apps/ocbc/app/uploads/5_4f713c0e-22ce-11e9-841e-1c36bb1a4426/images/page_conv.jpg', 500)