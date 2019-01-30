import logging
import os
import pdfplumber
import re
import subprocess

from service.extract_data_service import translate_text


def convert_pdf_to_text(pdf_path, x=None, width=None, height = None, y = 0):
    pdf_text_cmd = "pdftotext -layout -htmlmeta "
    if x is not None:
        pdf_text_cmd = pdf_text_cmd + " -x " + str(x) + " -y " + str(y) + " -W " + str(int(width)) + " -H " + str(int(height)) + " \"" + pdf_path + "\" - "
    else:
        pdf_text_cmd = pdf_text_cmd + " \"" + pdf_path + "\" - "
    pdf_text_process = subprocess.Popen(pdf_text_cmd, shell=True, stdout=subprocess.PIPE)
    text = pdf_text_process.communicate()[0]
    text = text.replace(b'\x0c', b'')
    return text


def find_dimensions_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
        if first_page is not None:
            width = first_page.width
            height = first_page.height
            return width, height
    except Exception:
        logging.error("PDFPlumber didn't read the pddf.")


def preprocess(data):
    spaces = re.findall(r'[ ]{2,}', data)
    for space in spaces:
        data = data.replace(space, '*' * (len(space)), 1)
    file_data = data.split('\n')
    return file_data


def translate_file_text(text, lang):
    tranlstated_list = []
    for line in text:
        spaces = re.findall(r'[ ]{2,}', line)
        for space in spaces:
            line = line.replace(space, '*' * (len(space)), 1)

        line = line.replace('.', ' ')
        translated_line = translate_text(line, lang)
        translated_line = re.sub(r'(?<=[*])([ ])(?=[*])', '', translated_line)
        translated_line = re.sub(r'(?<=[*])([ ])(?=[A-Za-z0-9.])', '', translated_line)
        translated_line = re.sub(r'(?<=[A-Za-z0-9.])([ ])(?=[*])', '', translated_line)
        tranlstated_list.append(translated_line)
    return tranlstated_list


def process(file_data, lang):
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    final_data = []
    for h in file_data:
        print(">>>>>>>>>", h)
        polish_splitted = re.split('[*]+', h)
        print('----0----')
        if len(polish_splitted) > 1:
            print('----0.5----')
            remove_indices = []
            for p in polish_splitted:
                print("---1---", p)
                tr_text = translate_text(p, lang)
                print("---2---", tr_text)
                if p == '1':
                    break
                if len(p) > len(tr_text):
                    di = len(p) - len(tr_text)
                    tr_text = tr_text + str(di * '*')
                    h = h.replace(p, tr_text)
                else:
                    map_diff_with_pos = {}
                    di = len(tr_text) - len(p)
                    pos = h.find(p) + len(tr_text)
                    map_diff_with_pos['pos'] = pos
                    map_diff_with_pos['di'] = di
                    if di > 0:
                        remove_indices.append(map_diff_with_pos)
                    h = h.replace(p, tr_text)
            all_indices_to_remove = []
            for item in remove_indices:
                position = item['pos']
                differ = item['di']
                for i in range(differ):
                    all_indices_to_remove.append(position + i)
            updated_string = [x for i, x in enumerate(h) if i not in all_indices_to_remove]
            h = ''.join(updated_string)
        else:
            print('---***---', h, 'lang****', lang)
            tr_text = translate_text(h, lang)
            h = h.replace(h, tr_text)
        final_data.append(h)
    return final_data
    # final_data = []
    # for h, k in zip(file_data, tran_list):
    #     polish_splitted = re.split('[*]+', h)
    #     tran_splitted = re.split('[*]+', k)
    #     if len(polish_splitted) > 1:
    #         remove_indices = []
    #         for (p, q) in zip(polish_splitted, tran_splitted):
    #             tr_text = q
    #             if p == '1':
    #                 break
    #             if len(p) > len(tr_text):
    #                 di = len(p) - len(tr_text)
    #                 tr_text = tr_text + str(di * '*')
    #                 h = h.replace(p, tr_text)
    #             else:
    #                 map_diff_with_pos = {}
    #                 di = len(tr_text) - len(p)
    #                 pos = h.find(p) + len(tr_text)
    #                 map_diff_with_pos['pos'] = pos
    #                 map_diff_with_pos['di'] = di
    #                 if di > 0:
    #                     remove_indices.append(map_diff_with_pos)
    #                 h = h.replace(p, tr_text)
    #         all_indices_to_remove = []
    #         for item in remove_indices:
    #             position = item['pos']
    #             differ = item['di']
    #             for i in range(differ):
    #                 all_indices_to_remove.append(position + i)
    #         updated_string = [x for i, x in enumerate(h) if i not in all_indices_to_remove]
    #         h = ''.join(updated_string)
    #     else:
    #         tr_text = k
    #         h = h.replace(h, tr_text)
    #     final_data.append(h)
    # return final_data


def post_process(final_data):
    fin_data = '\n'.join(final_data)
    fin_data = fin_data.replace('*', ' ')
    return fin_data


def read_file(path):
    with open(path, 'r', encoding='utf-8') as input_file:
        text = input_file.readlines()
    with open(path, 'r', encoding='utf-8') as input_file1:
        data = input_file1.read()
    return text, data


def extract_text_for_polish(pdf_path, basename, html_path, lang):
    print("===1===", pdf_path, basename, html_path)
    if lang == "vi":
        width, height = find_dimensions_pdf(pdf_path)
        pdftotext_data = convert_pdf_to_text(pdf_path=pdf_path, x=0, width=int(width / 2) , height=height)
    else:
        print("===2===")
        pdftotext_data = convert_pdf_to_text(pdf_path=pdf_path)
    with open(os.path.join(html_path, basename + ".html"), "wb") as html_fp:
        html_fp.write(pdftotext_data)
    text, data = read_file(os.path.join(html_path, basename + ".html"))
    if lang == "en":
        final_data = data
    else:
        print("===3===")

        file_data = preprocess(data)
        print("===4===")
        # tranlstated_list = translate_file_text(text=text, lang=lang)
        final_data = process(file_data=file_data, lang=lang)
        print("===5===")

        # final_data = process(file_data=file_data, tran_list=tranlstated_list, lang=lang)
        final_data = post_process(final_data)
    with open(os.path.join(html_path, basename + ".html"), "w",
              encoding="utf-8") as html_fp:
        html_fp.write(final_data)


# def extract_text_for_vietnamese(pdf_path, basename, html_path, lang):
#     width, height = find_dimensions_pdf(pdf_path)
#     pdftotext_data_part_1 = convert_pdf_to_text(pdf_path=pdf_path, x=0, width=int(width / 2) , height=height)
#     pdftotext_data_part_2 = convert_pdf_to_text(pdf_path=pdf_path, x=int(width / 2), width=int(width / 2), height = height)
#     pdf_to_text_data_list = []
#     pdf_to_text_data_list.append(pdftotext_data_part_1)
#     pdf_to_text_data_list.append(pdftotext_data_part_2)
#     for i, pdf_data_part in enumerate(pdf_to_text_data_list):
#         with open(os.path.join(html_path, basename + "_" + str(i) + ".html"), "wb") as html_fp:
#             html_fp.write(pdf_data_part)
#         text, data = read_file(os.path.join(html_path, basename + "_" + str(i) + ".html"))
#         file_data = preprocess(data)
#         tranlstated_list = translate_file_text(text=text, lang=lang)
#         final_data = process(file_data=file_data, tran_list=tranlstated_list, lang=lang)
#         final_data = post_process(final_data)
#         with open(os.path.join(html_path, basename + ".html"), "a",
#                   encoding="utf-8") as html_fp:
#             html_fp.write(final_data)
