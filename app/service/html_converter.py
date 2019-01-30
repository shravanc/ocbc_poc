from bs4 import BeautifulSoup

from service.table.structures import TableStructure


def convert_table_object_to_html(table_structure: TableStructure) -> str:
    td_style = "padding: 10px; border:3px solid black; white-space: pre-line"
    soup = BeautifulSoup("", "html.parser")

    table_tag = BeautifulSoup.new_tag(soup, "table", attrs={
        "border": "3px solid black",
    }, style="border-collapse: collapse; margin: 15px; ")

    for row in table_structure.table_cells:
        row_tag = BeautifulSoup.new_tag(soup, "tr")

        start_col = 0
        for cell in row:
            for _ in range(start_col, cell.column_no):
                empty_cell_tag = BeautifulSoup.new_tag(soup, "td", style=td_style)
                row_tag.append(empty_cell_tag)

            start_col = cell.column_no + cell.column_span

            cell_tag = BeautifulSoup.new_tag(soup, "td", style=td_style, attrs={
                "rowspan": cell.row_span,
                "colspan": cell.column_span,
            })
            cell_tag.string = cell.text
            row_tag.append(cell_tag)

        table_tag.append(row_tag)

    soup.append(table_tag)
    return str(soup)
