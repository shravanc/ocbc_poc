import math


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        result = self.x
        result = 31 * result + self.y
        return result

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, item):
        index = int(item)

        if index == 0:
            return self.x
        if index == 1:
            return self.y

    def __repr__(self):
        return "Point:({},{})".format(self.x, self.y)


class Line:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.start == other.start and self.end == other.end

    def __hash__(self):
        result = hash(self.start)
        result = 31 * result + hash(self.end)
        return result

    def __repr__(self):
        return "Line:(({},{}),({},{}))".format(self.start.x, self.start.y, self.end.x, self.end.y)

    def is_vertical(self):
        return self.start.x == self.end.x

    def is_horizontal(self):
        return self.start.y == self.end.y

    def length(self):
        return math.sqrt(math.pow(self.start.x - self.end.x, 2) + math.pow(self.start.y - self.end.y, 2))


class Intersection:
    def __init__(self, point, horizontal_line, vertical_line):
        self.point = point
        self.horizontal_line = horizontal_line
        self.vertical_line = vertical_line

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.point == other.point and \
               self.horizontal_line == other.horizontal_line and \
               self.vertical_line == other.vertical_line

    def __hash__(self):
        result = hash(self.point)
        result = 31 * result + hash(self.horizontal_line)
        result = 31 * result + hash(self.vertical_line)
        return result

    def __repr__(self):
        return f"Intersection: {self.point}: hor_line={self.horizontal_line}, ver_line={self.vertical_line}"


class Cell:
    def __init__(self, top_left, bottom_right, tl_v_line=None, tl_h_line=None, br_h_line=None, br_v_line=None):
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.tl_v_line = tl_v_line
        self.br_v_line = br_v_line
        self.tl_h_line = tl_h_line
        self.br_h_line = br_h_line

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.top_left == other.top_left and self.bottom_right == other.bottom_right

    def __hash__(self):
        result = hash(self.top_left)
        result = 31 * result + hash(self.bottom_right)
        return result

    def __repr__(self):
        return f"Cell: top_left={self.top_left}, bottom_right={self.bottom_right}"

    def area(self):
        return (self.bottom_right.x - self.top_left.x) * (self.bottom_right.y - self.top_left.y)


class TableCell:
    def __init__(self, cell, row_no, column_no, row_span, column_span, text=""):
        self.cell = cell
        self.row_no = row_no
        self.column_no = column_no
        self.row_span = row_span
        self.column_span = column_span
        self.text = text

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.cell == other.cell and \
               self.row_no == other.row_no and \
               self.column_no == other.column_no and \
               self.row_span == other.row_span and \
               self.column_span == other.column_span

    def __hash__(self):
        result = hash(self.cell)
        result = 31 * result + self.row_no
        result = 31 * result + self.column_no
        result = 31 * result + self.row_span
        result = 31 * result + self.column_span
        return result


class TableStructure:
    def __init__(self, table_cells, row_count, column_count, table_bbox=None):
        self.table_cells = table_cells
        self.row_count = row_count
        self.column_count = column_count
        self.table_bbox = table_bbox
