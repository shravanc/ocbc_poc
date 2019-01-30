import subprocess as sp

MIN_CHARS_FOR_MACHINE_GENERATED = 50


def is_machine_generated(pdf_path: str) -> bool:
    return len(_get_text_from_pdf(pdf_path)) >= MIN_CHARS_FOR_MACHINE_GENERATED


def _get_text_from_pdf(pdf_path: str) -> str:
    extract_text_cmd = [
        "pdftotext",
        pdf_path,
        "-"
    ]
    return sp.check_output(extract_text_cmd)
