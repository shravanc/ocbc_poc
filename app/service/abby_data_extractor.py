from .AbbyyOnlineSdk import AbbyyOnlineSdk, ProcessingSettings
import time
import pandas as pd
from utils import pairwise
from docx import Document
from os import path


def create_processor():
    processor = AbbyyOnlineSdk()
    processor.ApplicationId = "mrngstar"
    processor.Password = "OU0Eixew9trPorzq5Kmn/yQx"

    return processor


def extract_to_docx(page_pdf_path, docx_output_path):
    processor = create_processor()

    print("Uploading..")
    settings = ProcessingSettings()
    settings.Language = "English"
    settings.OutputFormat = "docx"
    task = processor.process_image(page_pdf_path, settings)
    if task is None:
        print("Error")
        return
    if task.Status == "NotEnoughCredits":
        print("Not enough credits to process the document. Please add more pages to your application's account.")
        return

    print("Id = {}".format(task.Id))
    print("Status = {}".format(task.Status))

    # Wait for the task to be completed
    print("Waiting..")
    # Note: it's recommended that your application waits at least 2 seconds
    # before making the first getTaskStatus request and also between such requests
    # for the same task. Making requests more often will not improve your
    # application performance.
    # Note: if your application queues several files and waits for them
    # it's recommended that you use listFinishedTasks instead (which is described
    # at http://ocrsdk.com/documentation/apireference/listFinishedTasks/).

    while task.is_active():
        time.sleep(5)
        print(".", end="")
        task = processor.get_task_status(task)

    print("Status = {}".format(task.Status))

    if task.Status == "Completed":
        if task.DownloadUrl is not None:
            processor.download_result(task, docx_output_path)
            print("Result was written to {}".format(docx_output_path))
    else:
        print("Error processing task")

    return docx_output_path


def extract_tables_from_docx(path):
    doc = Document(path)
    dfs = []

    for table in doc.tables:
        table_row_heights = [row.height for row in table.rows]
        avg_row_height = sum(table_row_heights) / len(table_row_heights)

        def dev_percent_from_avg(row):
            return abs(row.height - avg_row_height) / avg_row_height

        cells = [[cell.text for cell in row.cells] for row in table.rows if dev_percent_from_avg(row) < 1]
        dfs.append(pd.DataFrame(cells))

    dfs = [post_process(remove_adjacent_duplicate_columns(df)) for df in dfs]

    for df in dfs:
        df.columns = range(df.shape[1])
    return dfs


def post_process(df):
    return df.loc[:, (df == "$").sum() < 10]


def remove_adjacent_duplicate_columns(df):
    df = df.copy()
    new_df = pd.DataFrame()

    max_allowed_diffs = int(df.shape[0] * 0.1)

    for curr_col, next_col in pairwise(df[:-1]):
        if is_different(df[curr_col].values, df[next_col].values, max_allowed_diffs):
            new_df[curr_col] = df[curr_col]

    second_last_col, last_col = df.columns[-2], df.columns[-1]

    if is_different(df[second_last_col].values, df[last_col].values, max_allowed_diffs):
        new_df[second_last_col] = df[second_last_col]
        new_df[last_col] = df[last_col]
    else:
        new_df[second_last_col] = df[second_last_col]

    return new_df


def is_different(iterable_1, iterable_2, max_allowed_diffs):
    iterable_1 = list(iterable_1)
    iterable_2 = list(iterable_2)

    diff_count = 0
    for v1, v2 in zip(iterable_1, iterable_2):
        if v1 != v2:
            diff_count += 1
        if diff_count > max_allowed_diffs:
            return True
    return False


def get_tables_from_pdf(pdf_path):
    docx_output_path = path.join(path.dirname(pdf_path), f"{path.splitext(path.basename(pdf_path))[0]}.docx")
    extract_to_docx(pdf_path, docx_output_path)

    return extract_tables_from_docx(docx_output_path)
