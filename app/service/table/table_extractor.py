import itertools
from collections import defaultdict
from os import path
from typing import Tuple, List
from functools import partial

import cv2 as cv
import numpy as np
from PyPDF2 import PdfFileReader

import utils
from service.table.core import find_cells, get_table_structure, find_intersections
from service.table.structures import TableStructure, Line, Point

TuplePoint = Tuple[int, int]


def extract_tables(image_path: str, pdf_path: str, debug=False, debug_folder_path="") -> List[TableStructure]:
    debug = False
    debug_folder_path = "/Users/shravanc/Desktop/exp"
    image = cv.imread(image_path)
    if image is None:
        raise AssertionError('Error opening image: ' + image_path)

    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    _, thresholded_inverted_image = cv.threshold(gray_image, 127, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
    thresholded_inverted_image = cv.morphologyEx(thresholded_inverted_image, cv.MORPH_CLOSE,
                                                 np.full((5, 5), 255, dtype=np.uint8))

    # Open with horizontal and vertical kernels to find horizontal and vertical lines respectively
    kernel_length_factor = 25
    kernel_width = 1
    horizontal, hor_contours = _morph_open_and_find_contours(thresholded_inverted_image,
                                                             (
                                                                 int(thresholded_inverted_image.shape[
                                                                         1] / kernel_length_factor),
                                                                 kernel_width)
                                                             )
    vertical, ver_contours = _morph_open_and_find_contours(thresholded_inverted_image,
                                                           (
                                                               kernel_width,
                                                               int(thresholded_inverted_image.shape[
                                                                       0] / kernel_length_factor))
                                                           )
    contours, _ = process_thick_contours(hor_contours, ver_contours, gray_image, kernel_length_factor)

    lines_img = vertical + horizontal

    _, lines_contours, lines_contour_hierarchy = cv.findContours(lines_img, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)
    # No contours found
    if lines_contour_hierarchy is None:
        return []

    # Remove all contours that have no parents(h[3]). This will give all level 1 contours.
    parent_contours = [c for c, h in zip(lines_contours, lines_contour_hierarchy[0].tolist()) if h[3] == -1]

    if debug:
        # print("Debug is on------------------")
        debug_img_dict = {
            path.join(debug_folder_path, "hor_and_ver_contours.jpg"): cv.drawContours(np.copy(image),
                                                                                      hor_contours + ver_contours,
                                                                                      -1,
                                                                                      [0, 0, 255], thickness=2),
            path.join(debug_folder_path, "parent_contours.jpg"): cv.drawContours(np.copy(image), parent_contours, -1,
                                                                                 [0, 0, 255], thickness=2),
            path.join(debug_folder_path, "lines.jpg"): np.copy(lines_img),
            path.join(debug_folder_path, "vertical.jpg"): vertical,
            path.join(debug_folder_path, "horizontal.jpg"): horizontal,
            path.join(debug_folder_path, "thresholded_inverted.jpg"): np.copy(thresholded_inverted_image),
        }
        utils.save_images(debug_img_dict)

    total_area = image.shape[0] * image.shape[1]

    rects = []
    for i, contour in enumerate(parent_contours):

        # Maximum and minimum area check
        x, y, w, h = cv.boundingRect(cv.approxPolyDP(contour, 3, True))
        bounding_box_area = w * h
        relative_area = bounding_box_area / total_area * 100

        # print(f"Area of table = {relative_area}")
        if relative_area > 50 or relative_area < 9:
            continue

        # Passes all checks
        rects.append(utils.safe_pad_rect(((x, y), (x + w, y + h)), ((0, 0), (image.shape[1], image.shape[0])), 1))

    rect_to_contour_dict = defaultdict(list)
    for contour in contours:
        [ext_left, ext_top, ext_right, ext_bot] = _get_extreme_points(contour)
        for rect in rects:
            if _point_in_rect(ext_left, rect) \
                    or _point_in_rect(ext_top, rect) \
                    or _point_in_rect(ext_right, rect) \
                    or _point_in_rect(ext_bot, rect):
                rect_to_contour_dict[rect].append(contour)
                break

    image_width, image_height = image.shape[1], image.shape[0]
    pdf_width, pdf_height = _get_pdf_page_dimensions(pdf_path, 0)
    table_structures = []
    all_lines = []
    for rect, contours in rect_to_contour_dict.items():
        lines = utils.cv_contours_to_lines(contours)
        lines = _add_left_and_right_boundaries(lines, debug=True)
        lines = [utils.safe_pad_line(l, (image_width, image_height), 15) for l in lines]
        all_lines += lines

        intersections = find_intersections(lines)
        cells = find_cells(intersections)
        table_structure = get_table_structure(cells)
        table_structure.table_bbox = rect
        table_structures.append(table_structure)

    image_copy = np.copy(image)
    cv.rectangle(image_copy, (50, 50), (200, 200), [0, 0, 255], thickness=5)
    for row in table_structures[0].table_cells:
        for table_cell in row:
            cv.rectangle(image_copy, tuple(table_cell.cell.top_left), tuple(table_cell.cell.bottom_right), [0, 0, 255],
                         thickness=5)
    cv.imwrite(path.join(debug_folder_path, "cells.jpg"), image_copy)

    if debug:
        ds_lines_img = np.copy(image)

        for l in all_lines:
            cv.line(ds_lines_img, tuple(l.start), tuple(l.end), [0, 0, 255], 3)

        cv.imwrite(path.join(debug_folder_path, "ds_lines.jpg"), ds_lines_img)

    return sorted([_convert_table_structure_to_pdf_space(t, (image_width, image_height), (pdf_width, pdf_height))
                   for t in table_structures], key=lambda t: t.table_bbox[0][1])


def _add_left_and_right_boundaries(lines: List[Line],
                                   max_allowed_vertical_boundary_inset_percent=3, debug=False) -> List[Line]:
    hor_lines = [l for l in lines if l.is_horizontal()]
    ver_lines = [l for l in lines if l.is_vertical()]

    if len(ver_lines) == 0 or len(hor_lines) == 0:
        return lines

    # Ensure for horizontal lines start.x <= end.x
    for hor_line in hor_lines:
        if hor_line.start.x > hor_line.end.x:
            hor_line.start, hor_line.end = hor_line.end, hor_line.start

    # Ensure for vertical lines start.y <= end.y
    for ver_line in ver_lines:
        if ver_line.start.y > ver_line.end.y:
            ver_line.start, ver_line.end = ver_line.end, ver_line.start

    # Extreme points of the table
    top_max = min(hor_lines, key=lambda h_line: h_line.start.y).start.y
    bottom_max = max(hor_lines, key=lambda h_line: h_line.end.y).end.y
    left_max = min(hor_lines, key=lambda h_line: h_line.start.x).start.x
    right_max = max(hor_lines, key=lambda v_line: v_line.end.x).end.x

    width = right_max - left_max

    left_boundary_line_x = min([l.start.x for l in ver_lines])
    left_inset = abs(left_boundary_line_x - left_max) / width * 100
    # if debug:
    # print(f"left_inset={left_inset}")
    if left_inset > max_allowed_vertical_boundary_inset_percent:
        lines.append(Line(Point(left_max, top_max), Point(left_max, bottom_max)))
        # Extend horizontal lines to meet left boundary
        for l in hor_lines:
            l.start.x = left_max

    right_boundary_line_x = max([l.end.x for l in ver_lines])
    right_inset = abs(right_max - right_boundary_line_x) / width * 100

    # if debug:
    # print(f"right_inset={right_inset}")
    if right_inset > max_allowed_vertical_boundary_inset_percent:
        lines.append(Line(Point(right_max, top_max), Point(right_max, bottom_max)))
        # Extend horizontal lines to meet the right boundary
        for l in hor_lines:
            l.end.x = right_max

    return lines


def _get_extreme_points(contour: np.ndarray) -> Tuple[TuplePoint, TuplePoint, TuplePoint, TuplePoint]:
    ext_left = tuple(contour[contour[:, :, 0].argmin()][0])
    ext_right = tuple(contour[contour[:, :, 0].argmax()][0])
    ext_top = tuple(contour[contour[:, :, 1].argmin()][0])
    ext_bot = tuple(contour[contour[:, :, 1].argmax()][0])

    return ext_left, ext_top, ext_right, ext_bot


def _point_in_rect(point: TuplePoint, rect: [TuplePoint, TuplePoint]) -> bool:
    (tl_x, tl_y), (br_x, br_y) = rect
    x, y = point
    return tl_x <= x <= br_x and tl_y <= y <= br_y


def _morph_open_and_find_contours(img: np.ndarray, kernel_size: Tuple[int, int]):
    open_kernel = cv.getStructuringElement(cv.MORPH_RECT, kernel_size)
    opened_img = cv.morphologyEx(img, cv.MORPH_OPEN, open_kernel)
    _, contours, _ = cv.findContours(opened_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    return opened_img, contours


def _get_pdf_page_dimensions(pdf_file_path, page_no):
    """
    Gets the height and width of the pdf at the given page no after the rotation is applied. The default height and
    width are swapped when the pdf has a rotation of 90/270(vertical).
    :param pdf_file_path: File path of the input pdf
    :param page_no: Page no whose dimensions are returned
    :return: A tuple of the form (width, height)
    """
    with open(pdf_file_path, 'rb') as file:
        pdf_file = PdfFileReader(file).getPage(page_no)
        media_box = pdf_file.mediaBox
        rotation = pdf_file.get('/Rotate')

        if utils.is_horizontal_orientation(rotation):
            w, h = media_box.getWidth(), media_box.getHeight()
        else:
            w, h = media_box.getHeight(), media_box.getWidth()

        return w, h


def _convert_coordinate_system(point, dest_space_width, dest_space_height,
                               src_space_width, src_space_height):
    """
    Converts a point from src coordinate system to dest coordinate system.
    :point (x,y) in the src coordinate system
    :param dest_space_width: Height of the dest coordinate system
    :param dest_space_height: Width of the dest coordinate system
    :param src_space_width: Height of the source coordinate system
    :param src_space_height: Width of the source coordinate system
    :return: a tuple (x,y) mapped to the dest coordinate system
    """
    x, y = point
    return x * dest_space_width / src_space_width, y * dest_space_height / src_space_height


def _convert_table_structure_to_pdf_space(table_structure: TableStructure, image_shape: Tuple[int, int],
                                          pdf_shape: Tuple[int, int]) -> TableStructure:
    coords_convert = partial(_convert_coordinate_system, dest_space_width=pdf_shape[0],
                             dest_space_height=pdf_shape[1], src_space_width=image_shape[0],
                             src_space_height=image_shape[1])

    table_structure.table_bbox = coords_convert(table_structure.table_bbox[0]), \
                                 coords_convert(table_structure.table_bbox[1])

    for row in table_structure.table_cells:
        for table_cell in row:
            table_cell.cell.top_left = coords_convert(table_cell.cell.top_left)
            table_cell.cell.bottom_right = coords_convert(table_cell.cell.bottom_right)

    return table_structure


def _slice_thick_contours(img, kernel_size):
    open_kernel = cv.getStructuringElement(cv.MORPH_RECT, kernel_size)
    sliced_img = cv.morphologyEx(img, cv.MORPH_OPEN, open_kernel)

    dilate_kernel = cv.getStructuringElement(cv.MORPH_RECT, (7, 7))
    sliced_img = cv.morphologyEx(sliced_img, cv.MORPH_DILATE, dilate_kernel)

    _, contours, _ = cv.findContours(sliced_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    return sliced_img, contours


def process_thick_contours(hor_contours, ver_contours, img, slice_kernel_length_factor):
    thickness_dimension = 50

    sliced_contours = []

    thick_hor_contours = []
    for contour in hor_contours:
        _, _, _, height = cv.boundingRect(contour)

        if height > thickness_dimension:
            thick_hor_contours.append(contour)
        else:
            sliced_contours.append(contour)
    if len(thick_hor_contours) != 0:
        copy = np.zeros_like(img)

        for contour in thick_hor_contours:
            cv.drawContours(copy, [contour], 0, [255, 255, 255])

        ver_open_kernel_size = (int(img.shape[1] / slice_kernel_length_factor), 1)
        _, sliced_hor_contours = _slice_thick_contours(copy, ver_open_kernel_size)
        sliced_contours += sliced_hor_contours

    thick_ver_contours = []
    for contour in ver_contours:
        _, _, width, _ = cv.boundingRect(contour)

        if width > thickness_dimension:
            thick_ver_contours.append(contour)
        else:
            sliced_contours.append(contour)
    if len(thick_ver_contours) != 0:
        copy = np.zeros_like(img)

        for contour in thick_ver_contours:
            cv.drawContours(copy, [contour], 0, [255, 255, 255])

        hor_open_kernel_size = (1, int(img.shape[0] / slice_kernel_length_factor))
        _, sliced_ver_contours = _slice_thick_contours(copy, hor_open_kernel_size)
        sliced_contours += sliced_ver_contours

    return sliced_contours, thick_hor_contours + thick_ver_contours
