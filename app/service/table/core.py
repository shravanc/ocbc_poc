from enum import Enum
import functools

from service.table.structures import Point, Cell, TableCell, TableStructure, Intersection, Line
from sortedcontainers import SortedList, SortedListWithKey


class _PointOfInterest:
    class PointType(Enum):
        HORIZONTAL_LEFT = 1
        HORIZONTAL_RIGHT = 2
        VERTICAL = 3

    def __init__(self, point_type, x, line):
        self.point_type = point_type
        self.x = x
        self.line = line

    def __repr__(self):
        return f"POI: x={self.x} | line={self.line} | type={self.point_type}"


def find_intersections(lines):
    def poi_sort_x(poi, other):
        if poi.x == other.x:
            if poi.point_type == _PointOfInterest.PointType.VERTICAL and \
                    other.point_type == _PointOfInterest.PointType.HORIZONTAL_LEFT:
                return 1
            elif poi.point_type == _PointOfInterest.PointType.HORIZONTAL_LEFT and \
                    other.point_type == _PointOfInterest.PointType.VERTICAL:
                return -1
            elif poi.point_type == _PointOfInterest.PointType.VERTICAL and \
                    other.point_type == _PointOfInterest.PointType.HORIZONTAL_RIGHT:
                return -1
            elif poi.point_type == _PointOfInterest.PointType.HORIZONTAL_RIGHT and \
                    other.point_type == _PointOfInterest.PointType.VERTICAL:
                return 1
            elif poi.point_type == _PointOfInterest.PointType.HORIZONTAL_RIGHT and \
                    other.point_type == _PointOfInterest.PointType.HORIZONTAL_LEFT:
                return 1
            elif poi.point_type == _PointOfInterest.PointType.HORIZONTAL_LEFT and \
                    other.point_type == _PointOfInterest.PointType.HORIZONTAL_RIGHT:
                return -1
            else:
                return 0
        else:
            if poi.x > other.x:
                return 1
            else:
                return -1

    vertical_lines = []
    horizontal_lines = []

    for line in lines:
        if line.is_vertical():
            vertical_lines.append(line)
        elif line.is_horizontal():
            if line.start.x > line.end.x:
                horizontal_lines.append(Line(start=line.end, end=line.start))
            else:
                horizontal_lines.append(line)
        else:
            raise ValueError("Find intersections supports horizontal and vertical lines")

    points_of_interest = []

    for h_line in horizontal_lines:
        points_of_interest.append(_PointOfInterest(_PointOfInterest.PointType.HORIZONTAL_LEFT, h_line.start.x, h_line))
        points_of_interest.append(_PointOfInterest(_PointOfInterest.PointType.HORIZONTAL_RIGHT, h_line.end.x, h_line))

    for v_line in vertical_lines:
        points_of_interest.append(_PointOfInterest(_PointOfInterest.PointType.VERTICAL, v_line.start.x, v_line))

    points_of_interest.sort(key=functools.cmp_to_key(poi_sort_x))

    line_sweep_hor_list = SortedListWithKey(key=lambda l: l.start.y)
    intersections = []
    for poi in points_of_interest:
        if poi.point_type == _PointOfInterest.PointType.HORIZONTAL_LEFT:
            line_sweep_hor_list.add(poi.line)
        elif poi.point_type == _PointOfInterest.PointType.HORIZONTAL_RIGHT:
            line_sweep_hor_list.remove(poi.line)
        else:
            for hor_line in line_sweep_hor_list.irange_key(min_key=poi.line.start.y, max_key=poi.line.end.y):
                intersections.append(Intersection(Point(poi.line.start.x, hor_line.start.y), hor_line, poi.line))

    return intersections


def find_cells(intersections):
    intersection_point_to_lines_dict = {}
    for intersection in intersections:
        intersection_point_to_lines_dict[intersection.point] = (intersection.horizontal_line,
                                                                intersection.vertical_line)

    intersection_points = [intersection.point for intersection in intersections]
    intersection_points.sort(key=lambda point: (point.y, point.x))

    def _find_smallest_cell(index):
        top_left = intersection_points[index]

        h_line, v_line = intersection_point_to_lines_dict[top_left]

        points_below = [point for point in intersection_points[index + 1:] if
                        top_left.x == point.x and point.y > top_left.y]
        points_right = [point for point in intersection_points[index + 1:] if
                        top_left.y == point.y and point.x > top_left.x]

        for p_below in points_below:
            if intersection_point_to_lines_dict[p_below][1] != v_line:
                continue
            for p_right in points_right:
                if intersection_point_to_lines_dict[p_right][0] != h_line:
                    continue

                btm_right = Point(p_right.x, p_below.y)

                if btm_right in intersection_point_to_lines_dict:
                    h_line_btm_right, v_line_btm_right = intersection_point_to_lines_dict[btm_right]

                    if h_line_btm_right == intersection_point_to_lines_dict[p_below][0] and \
                            v_line_btm_right == intersection_point_to_lines_dict[p_right][1]:
                        return Cell(top_left, btm_right,
                                    tl_v_line=v_line, tl_h_line=h_line,
                                    br_v_line=v_line_btm_right, br_h_line=h_line_btm_right)

    cell_gen = (_find_smallest_cell(i) for i in range(len(intersection_points)))

    return list(filter(None, cell_gen))


def get_table_structure(cells):
    row_lines = set()
    col_lines = set()

    for cell in cells:
        row_lines.add(cell.top_left.y)
        row_lines.add(cell.bottom_right.y)
        col_lines.add(cell.top_left.x)
        col_lines.add(cell.bottom_right.x)

    row_lines = SortedList(row_lines)
    col_lines = SortedList(col_lines)

    table_cells = [list() for _ in range(len(row_lines) - 1)]
    for cell in cells:
        row_no = row_lines.index(cell.top_left.y)
        col_no = col_lines.index(cell.top_left.x)

        row_span = row_lines.index(cell.bottom_right.y) - row_no
        col_span = col_lines.index(cell.bottom_right.x) - col_no

        table_cells[row_no].append(TableCell(cell, row_no, col_no, row_span, col_span))

    table_cells = [sorted(row, key=lambda c: c.column_no) for row in table_cells]
    return TableStructure(table_cells, len(row_lines) - 1, len(col_lines) - 1)
