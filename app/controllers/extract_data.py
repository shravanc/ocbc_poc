import glob
import logging
import os

from natsort import natsorted

from constant import PDF_UPLOAD_DIRECTORY, AWS_INSTANCE_IP, DEFAULT_PARSE_METHOD
from exceptions.exceptions_handler import *
from log import timeit
from service.abby_data_extractor import get_tables_from_pdf
from service.extract_data_service import map_table_data_to_text
from service.html_converter import convert_table_object_to_html
from service.pdf_split_service import PDFSplitService
from service.table import table_extractor as te
from service.translate_service import extract_text_for_polish
from utils import formulate_response
from service.machine_vs_scanned import is_machine_generated
from service.ocbc_regex_list import fetch_fields

import subprocess
from lib.test import extract_tables


from models.ocbc_metadata import Ocbc
from tasks import pdf_page_to_image_task, pdf_page_to_regular_image_task, pdf_page_to_lower_dpi_image_task

from lib.check_box_data import CheckBox, CoOrdinate, get_cordinates
from lib.my_google_vision import MyGoogleVision

def setup_upload_folders(page_folder_location, file_location):
    required_folders = ['pages', 'images', 'html', 'text', 'regular_image', 'converted_image']
    paths = []
    for folder in required_folders:
        path = os.path.join(page_folder_location, folder)
        if not os.path.exists(path):
            os.makedirs(path)
        paths.append(path)
    return paths

def get_pdfs(start_page, last_page, file_location, pdf_pages_path):
    pdf_split_service = PDFSplitService(start_page, last_page)
    pdf_split_service.split_pdf(file_location, pdf_pages_path)
    pdfs = natsorted(glob.glob(pdf_pages_path + "/*.pdf"))
    return pdfs

def get_pdfs_and_imgs(start_page, last_page, file_location, pdf_pages_path, images_path, regular_image_path, converted_image_path):
    pdf_split_service = PDFSplitService(start_page, last_page)
    pdf_split_service.split_pdf(file_location, pdf_pages_path)
    pdfs = natsorted(glob.glob(pdf_pages_path + "/*.pdf"))

    pdf_pages = []
    # image_paths = []
    # regular_image_paths []
    for pdf in pdfs:
        basename = os.path.basename(pdf).split('.')[0]
        pdf_pages.append(pdf)
        # image_paths.append(os.path.join(images_path, basename + ".jpg"))
        # regular_image_paths.append(os.path.join(regular_image_path, basename + ".jpg"))
        pdf_page_to_image_task(pdf, os.path.join(images_path, basename + ".jpg"))
        pdf_page_to_regular_image_task(pdf, os.path.join(regular_image_path, basename + ".jpg") )
        pdf_page_to_lower_dpi_image_task(pdf, os.path.join(converted_image_path, basename + ".jpg") )

    # res = pdf_page_to_image_task.chunks( zip( pdf_pages, image_paths), 3 )()
    # res.join()
    imgs = natsorted(glob.glob(images_path + "/page-*.jpg"))
    r_imgs = natsorted(glob.glob( regular_image_path + "/page-*.jpg"))
    c_imgs = natsorted(glob.glob( converted_image_path + '/page-*.jpg'))
    return [pdfs, imgs, r_imgs, c_imgs]

def create_html(tool, html_path, basename, tables):
    if tool == 'abby':
        with open(os.path.join(html_path, basename + ".html"), "w",
                          encoding="utf-8") as html_fp:
                    # abby_tables[0].to_csv(os.path.join(html_path, basename + ".csv"), sep=',', encoding='utf-8')
                    html_table = tables[0].to_html(index=False, classes="td, th {padding: 15px;}", header=False, border=3)
                    if html_table is not None:
                        html_fp.write(html_table)
    else:
        with open(os.path.join(html_path, basename + ".html"), "w",
                          encoding="utf-8") as html_fp:
                    for table in tables:
                        html_table = convert_table_object_to_html(table)
                        if html_table is not None:
                            html_fp.write(html_table)


def convert_pdf_to_text(pdf_path, filename, raw=False):
    pdf_text_cmd = f"pdftotext" + " " + f"{'-raw' if raw else '-layout'}" + " " + pdf_path + " " + filename
    # print("PDFTO_TEXT_COMMAND---------->", pdf_text_cmd)
    pdf_text_process = subprocess.Popen(pdf_text_cmd, shell=True, stdout=subprocess.PIPE)
    text = pdf_text_process.communicate()[0]
    return text

def parse_scanned_doc(page_folder_location, file_location, start_page, last_page, lang):
    # print("***11***")
    pdf_pages_path, images_path, html_path, text_path, regular_image_path, converted_image_path = setup_upload_folders(page_folder_location, file_location)
    # pdfs = get_pdfs(start_page, last_page, file_location, pdf_pages_path)
    pdfs, imgs, r_imgs, c_imgs = get_pdfs_and_imgs(start_page, last_page, file_location, pdf_pages_path, images_path, regular_image_path, converted_image_path)
    # print("***12***")
    prediction = None
    check_box = None
    for img, pdf, r_img, c_img in zip(imgs, pdfs, r_imgs, c_imgs):
        print("***12.5***")
        basename = os.path.basename(pdf).split('.')[0]

        if DEFAULT_PARSE_METHOD == 'abby':
            # print("***13***")
            abby_tables = get_tables_from_pdf(pdf)
            # print(abby_tables)
            if len(abby_tables) > 0:
                # print("***13.5***")
                create_html('abby', html_path, basename, abby_tables)
            else:
                # print("***13.6***")
                extract_text_for_polish(pdf, basename, html_path, lang)
        else:
            print("***14***", img)
            gv = MyGoogleVision(r_img, 1)
            gv.get_visioned()
            gv.make_sense()
            prediction = fetch_fields(gv, Ocbc())

            check_box = extract_tables(c_img, pdf)

            check_box.extract_text()
            check_box.generate_response()
            print(check_box.response)

            # print('-----------VISION-RESPONSE------------')
            print(gv.display())
            convert_pdf_to_text(pdf, (text_path + "page-1.txt") )
            # print("---------------PDFTO_TEXT--------------")
            tables = te.extract_tables(img, pdf,
                                       debug=False,
                                       debug_folder_path=images_path)

            if len(tables) > 0:
                # print("***15***")
                map_table_data_to_text(tables, pdf, lang, gv, prediction)
                print("--------->Prediction-------->", prediction.to_json())
                # print("***15.6***")
                create_html('tesseract', html_path, basename, tables)
                # print('***15.7***')
            elif len(tables) == 0:
                # print("***16***")
                abby_tables = get_tables_from_pdf(pdf)
                if len(abby_tables) > 0:
                    # print("***17***")
                    create_html('abby', html_path, basename, abby_tables)
                else:
                    extract_text_for_polish(pdf, basename, html_path, lang)


    print("**********************************EXTRACTION*************************************")
    print("prediction-->", prediction)
    print("check_box--->", check_box)
    print("**********************************EXTRACTION*************************************")
    return [prediction, check_box]


def parse_machine_generated_doc(page_folder_location, file_location, start_page, last_page, lang):
    pdf_pages_path, images_path, html_path = setup_upload_folders(page_folder_location, file_location)
    pdfs, imgs = get_pdfs_and_imgs(start_page, last_page, file_location, pdf_pages_path, images_path)

    for img, pdf in zip(imgs, pdfs):
            basename = os.path.basename(pdf).split('.')[0]
            tables = te.extract_tables(img, pdf,
                                       debug=False,
                                       debug_folder_path=images_path)

            if len(tables) > 0:
                map_table_data_to_text(tables, pdf, lang)
                create_html('tesseract', html_path, basename, tables)
            elif len(tables) == 0:
                abby_tables = get_tables_from_pdf(pdf)
                if len(abby_tables) > 0:
                    create_html('abby', html_path, basename, abby_tables)
                else:
                    extract_text_for_polish(pdf, basename, html_path, lang)

@timeit
def extract_translated_data(filename, file_location, start_page, last_page=None, lang='ne'):
    # print("***1***")
    try:
        # Create Parent PDF Directory
        page_folder_location = os.path.join(PDF_UPLOAD_DIRECTORY, filename)
        if PDF_UPLOAD_DIRECTORY is not None and file_location is not None:
            if not os.path.exists(page_folder_location):
                os.makedirs(page_folder_location)

        # print("***2***")
        if last_page:
            if last_page < start_page:
                return formulate_response("Start page cannot be greater than last page", 500, "Failed")
        else:
            last_page = start_page

        # print("***3***")
        if  False: #is_machine_generated((page_folder_location+'.pdf')):
            logging.info("Machined document")
            parse_machine_generated_doc(page_folder_location, file_location, start_page, last_page, lang)
        else:
            logging.info("Scanned document")
            prediction, check_box = parse_scanned_doc(page_folder_location, file_location, start_page, last_page, lang)

        # print("***4***")
        return [prediction, check_box]
        # return formulate_result(page_folder_location)

    except CustomClassifierException as e:
        print("ERROR--->1", e)
        logging.error("Error {} has occurred in controller".format(e))
        return e.response, e.http_code

    except Exception as e:
        print("ERROR--->2", e)
        logging.error("Error in service = {}".format(e), exc_info=True)
        return InternalServerErrorException(error_code=500,
                                            error_message="Data Extraction failed!").response, 500
    finally:
        logging.info("API Call Finished Successfully - 200")


def formulate_result(pdf_folder_location):
    pdf_pages_path = os.path.join(pdf_folder_location, "pages")
    pdfs = sorted(glob.glob(pdf_pages_path + "/*.pdf"))
    html_pages_path = os.path.join(pdf_folder_location, "html")
    htmls = sorted(glob.glob(html_pages_path + "/*.html"))
    datalist = []
    for pdf, html in zip(pdfs, htmls):
        data = {}
        html = html.replace(PDF_UPLOAD_DIRECTORY, AWS_INSTANCE_IP)
        pdf = pdf.replace(PDF_UPLOAD_DIRECTORY, AWS_INSTANCE_IP)
        data["page_no"] = os.path.basename(pdf).split('.')[0]
        data["pdf_path"] = pdf
        data["html_path"] = html
        datalist.append(data)
    return datalist
