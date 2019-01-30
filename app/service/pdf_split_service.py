import logging
import os
import subprocess

from constant import APP_MODEL, RESPONSE_TEMPLATE_JSON, ERR_FILE_READ, ERR_FILE_READ_DESC
from exceptions.exceptions_handler import *


class PDFSplitService:

    def __init__(self, start_page, last_page):
        self.start_page = start_page
        self.last_page = last_page

    def split_pdf(self, file_location, page_dir_location):
        """
        Take a PDF and split into individual pages.

        @param doc_id: File name of the PDF.
        @type doc_id: str
        @param file_location: Folder path to the PDF.
        @type file_location: str
        @return: A list of pdf page ids with absolulte path.
        @rtype: list(str)
        """

        data = self.get_response()
        pages_array = []
        try:
            if page_dir_location is not None and file_location is not None:
                if not os.path.exists(page_dir_location):
                    os.makedirs(page_dir_location)
            self.pdf_split_with_pdfseparate(file_location, page_dir_location)

        except FileNotFoundError as e:
            logging.error("Error {} has occured in controller".format(e), exc_info=True)
            raise FileNotFoundErrorException(error_code=ERR_FILE_READ,
                                             error_message=ERR_FILE_READ_DESC, http_status_code=INTERNAL_SERVER_ERROR)

        except Exception as e:
            # Fall back to pdfseparate if PyPDF2 fails
            page_count = self.pdf_split_with_pdfseparate(file_location, page_dir_location)
            if page_count is not -1:
                page_count = page_count.rstrip().decode("utf-8")
                for i in range(int(page_count)):
                    filename = "page-%s.pdf" % str(i + 1)
                    pages_array.append(os.path.join(page_dir_location, filename))
            else:
                logging.error("Error in service = {}".format(e), exc_info=True)
                raise InternalServerErrorException(error_code=INTERNAL_SERVER_ERROR,
                                                   error_message="PDF couldn't be splitted")

        data["pages"] = pages_array
        return data

    def get_response(self):
        try:
            with open(os.path.join(APP_MODEL, RESPONSE_TEMPLATE_JSON), 'r') as f:
                datastore = json.load(f)
                data = datastore["data"]
            return data
        except FileNotFoundError as e:
            raise FileNotFoundErrorException(error_code=ERR_FILE_READ,
                                             error_message=ERR_FILE_READ_DESC, http_status_code=INTERNAL_SERVER_ERROR)

    def pdf_split_with_pdfseparate(self, file_location, page_dir_location):
        """
        Fall back to PDFSeparate if PyPDF2 fails.
        :param file_location: PDF File location
        :type file_location: str
        :param page_dir_location: Location to store pdf pages
        :type page_dir_location: str
        :return: Page count
        :rtype: int
        """
        pdf_separate_cmd = "pdfseparate -f " + str(self.start_page) + " -l " + str(
            self.last_page) + " \"" + file_location + "\" \"" + page_dir_location + "/" + "page-%d.pdf\""
        pdf_page_count_cmd = "pdfinfo \"" + file_location + "\" | grep Pages | awk '{print $2}'"
        pdf_separate_process = subprocess.Popen(pdf_separate_cmd, shell=True, stdout=subprocess.PIPE)
        pdf_separate_process.communicate()
        pdf_page_count_process = subprocess.Popen(pdf_page_count_cmd, shell=True, stdout=subprocess.PIPE)
        page_count = pdf_page_count_process.communicate()
        if pdf_page_count_process.returncode == 0 and pdf_separate_process.returncode == 0:
            return page_count[0]
        else:
            return -1
