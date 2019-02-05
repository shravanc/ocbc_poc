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

from tasks import extract_cell_data
from celery import group
from enum import Enum

# def create_image_from_pdf(file_location, page_folder_location, start_page, last_page):
#     if page_folder_location is not None and file_location is not None:
#         if not os.path.exists(os.path.join(page_folder_location, "images")):
#             os.makedirs(os.path.join(page_folder_location, "images"))
#
#     pdf_image_cmd = "pdftocairo -jpeg -r 300 -f " + str(start_page) + " -l " + str(
#         last_page) + " " + file_location + " " + os.path.join(page_folder_location, "images") + "/" + "page"
#     pdf_image_process = subprocess.Popen(pdf_image_cmd, shell=True, stdout=subprocess.PIPE)
#     pdf_image_process.communicate()
#     if pdf_image_process.returncode != 0:
#         return False
#     return True

def update_translated_text_to_cells(data, tables):
    results = []
    for d1 in data:
        results = results + d1

    index = 0
    for ti, table in enumerate(tables):
        table_cells = table.table_cells
        for ri, row in enumerate(table_cells):
            for ci, col in enumerate(row):
                col.text = results[index]
                print(f"Table->{t1}, Row->{ri}, Col->{ci}, ----->Text{col.text}")
                index += 1

def construct_command(col, pdf_path):
    co_ordinates = {"x": int(col.cell.top_left[0]),
                    "y": int(col.cell.top_left[1]),
                    "w": (int((col.cell.bottom_right[0]) - (col.cell.top_left[0]))),
                    "h": int((col.cell.bottom_right[1]) - (col.cell.top_left[1]))
                    }
    return [co_ordinates, "pdftotext -layout -x " + str(int(col.cell.top_left[0])) + " -y " + str(
                int(col.cell.top_left[1])) + " -W " + str(int(
                (col.cell.bottom_right[0]) - (col.cell.top_left[0]))) + " -H " + str(int(
                (col.cell.bottom_right[1]) - (col.cell.top_left[1]))) + " \"" + pdf_path + "\" - "]

def map_table_data_to_text(tables, pdf_path, lang, gv, prediction):
    pdf_text_cmd_list = []
    co_ordinates_list = []
    gv_list = []
    texts = []
    #print('MapTableDataToText----1')
    for ti, table in enumerate(tables):
        table_cells = table.table_cells
        for ri, row in enumerate(table_cells):
            for ci, col in enumerate(row):
                print("PDF_TO_TEXT_COMMAND------>" )

                co_ordinates, pdf_text_cmd = construct_command(col, pdf_path)
                co_ordinates_list.append(co_ordinates)
                pdf_text_cmd_list.append(pdf_text_cmd)
                col.text = extract_cell_data(pdf_path, pdf_text_cmd, lang, co_ordinates, gv)
                if ri >= 1 and ci == 0:
                    if len(col.text) >= 1:
                        prediction.gaurantors.append(col.text)
                #print(f"Table->{ti}, Row->{ri}, Col->{ci}, ----->Text{col.text}")

    # print('MapTableDataToText----10')
    # pdf_path_list = [ pdf_path for i in range( len(pdf_text_cmd_list) ) ]
    # lang_list     = [ lang for i in range( len(pdf_text_cmd_list) ) ]
    # vision_list = [ gv for i in range( len(pdf_text_cmd_list) ) ]
    # cordinates_list = [ ord for i in range( len(co_ordinates_list) ) ]
    #
    # print('MapTableDataToText----11')
    # res = extract_cell_data.chunks( zip( pdf_path_list, pdf_text_cmd_list, lang_list, cordinates_list, vision_list), 3 )()
    # print('MapTableDataToText----12')
    # data = res.join()
    # print('MapTableDataToText----13')
    # update_translated_text_to_cells(data, tables)

def translate_text(text, lang):
    print("+++++11+++++")
    # [START translate_translate_text]
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    translate_client = translate.Client()
    print("+++++12+++++")
    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')
    print("+++++13+++++", text)
    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(
        text, source_language=lang, target_language='en')
    print("+++++14+++++")
    return result['translatedText']
