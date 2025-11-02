from typing import List, Optional, Dict, Any, Union
import re


def pad_columns(
    rows: List[List[str]],
    align_last: bool = False,
    separator_space: bool = True,
    max_width: Optional[int] = None,
    alignment: str = 'left',
    auto_align_numeric: bool = True,
) -> List[List[str]]:
    """
    Pads each column in a list of lists so that all values align neatly.

    Args:
        rows: A list of lists representing tabular data.
        separator_space: If True, adds extra space around the value for separation.
        max_width: If set, limits the maximum padding width for any column.
        alignment: Default alignment for text ("left", "right", "center").
        auto_align_numeric: If True, automatically right-aligns numeric columns.

    Returns:
        A new list of lists with padded string values.
    """
    if not rows:
        return []

    # Convert all entries to strings
    str_rows = [[str(cell) for cell in row] for row in rows]
    num_cols = max(len(row) for row in str_rows)

    # Detect numeric columns
    def is_numeric(value: str) -> bool:
        value = value.strip()
        return value.replace('.', '', 1).replace('-', '', 1).isdigit()

    numeric_cols = []
    for col in range(num_cols):
        col_values = [r[col].strip() for r in str_rows[1:] if col < len(r)]
        numeric_cols.append(all(is_numeric(v) for v in col_values if v != ''))

    # Compute max width per column
    col_widths = []
    for col in range(num_cols):
        max_len = max((len(row[col]) if col < len(row) else 0) for row in str_rows)
        if max_width is not None:
            max_len = min(max_len, max_width)
        col_widths.append(max_len)

    # Apply alignment and padding
    padded_rows = []
    for row in str_rows:
        padded = []
        for i, cell in enumerate(row):
            width = col_widths[i]
            # Determine effective alignment
            align_mode = alignment
            if auto_align_numeric and numeric_cols[i]:
                align_mode = 'right'

            first_col = i == 0
            last_col = i == len(row) - 1
            if align_mode == 'right':
                padded_cell = cell.rjust(width)
            elif align_mode == 'center':
                padded_cell = cell.center(width)
            elif align_mode == 'left':
                padded_cell = cell.ljust(width)
            else:
                ValueError(f'Unrecognized alignment mode {alignment}')
                padded_cell += ' '

            if separator_space:
                if not first_col:
                    padded_cell = ' ' + padded_cell
                if not last_col:
                    padded_cell += ' '

            padded.append(padded_cell)
        padded_rows.append(padded)

    return padded_rows


def parse_markdown_table(md: str) -> List[List[str]]:
    """
    Parse a Markdown table into a list of lists.

    Example input:
        | Name  | Age | City  |
        |-------|-----|-------|
        | Alice | 30  | Denver|
        | Bob   | 9   | LA    |

    Returns:
        [['Name', 'Age', 'City'],
         ['Alice', '30', 'Denver'],
         ['Bob', '9', 'LA']]
    """
    lines = [line.strip() for line in md.strip().splitlines() if line.strip()]
    if not lines:
        return []

    table = []
    for line in lines:
        # Skip the separator line (e.g., | --- | --- |)
        if re.match(r'^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$', line):
            continue

        # Split columns, trimming each cell
        parts = [cell.strip() for cell in re.split(r'\s*\|\s*', line.strip('| '))]
        table.append(parts)

    return table


def markdown_table_dictreader(md: str) -> List[Dict[str, str]]:
    """
    Parses a Markdown table and returns a list of dicts like csv.DictReader.
    The first row is treated as the header.
    """
    table = parse_markdown_table(md)
    if not table or len(table) < 2:
        return []

    headers = table[0]
    data_rows = table[1:]

    dict_rows = []
    for row in data_rows:
        row_dict = {
            headers[i]: row[i] if i < len(row) else '' for i in range(len(headers))
        }
        dict_rows.append(row_dict)

    return dict_rows


def _alignment_marker(align: Optional[str]) -> str:
    if align == 'left':
        return ':---'
    elif align == 'right':
        return '---:'
    elif align == 'center':
        return ':---:'
    return '---'


def _infer_alignments(rows: List[List[Any]], side='right') -> List[str]:
    """Infer alignments per column: right for numeric columns, left otherwise."""
    if not rows or len(rows) < 2:
        return ['left'] * (len(rows[0]) if rows else 0)

    num_cols = len(rows[0])
    alignments = []

    for col_idx in range(num_cols):
        # Skip header row; only inspect data rows
        col_values = [r[col_idx] for r in rows[1:] if col_idx < len(r)]
        non_empty = [v for v in col_values if str(v).strip() != '']
        if non_empty and all(
            re.fullmatch(r'[-+]?\d*\.?\d+', str(v).strip()) for v in non_empty
        ):
            alignments.append(side)
        else:
            alignments.append('left')

    return alignments


def to_markdown_table(
    rows: List[List[Any]],
    align_last: bool = False,
    separator_space: bool = True,
    max_width: Optional[int] = None,
    alignments: Optional[List[str]] = None,
    auto_align_numeric: Optional[Union[bool, str]] = True,
) -> str:
    """
    Convert a list of lists into a Markdown table string.
    Auto-detects numeric columns for right alignment unless alignments are given.
    """
    if not rows:
        return ''

    str_rows = [[str(cell) for cell in row] for row in rows]
    padded = pad_columns(
        str_rows,
        align_last=align_last,
        separator_space=separator_space,
        max_width=max_width,
    )
    num_cols = len(padded[0])

    if alignments is None and auto_align_numeric:
        auto_align_numeric = (
            auto_align_numeric
            if auto_align_numeric in ('left', 'center', 'right')
            else 'right'
        )
        alignments = _infer_alignments(rows, side=auto_align_numeric)

    # TODO pad with dashes
    separators = [
        _alignment_marker(alignments[i]) if i < len(alignments) else '---'
        for i in range(num_cols)
    ]

    lines = []
    lines.append('| ' + ' | '.join(padded[0]) + ' |')
    lines.append('| ' + ' | '.join(separators) + ' |')
    for row in padded[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')

    return '\n'.join(lines)


def dicts_to_markdown_table(
    dict_rows: List[Dict[str, Any]],
    fieldnames: Optional[List[str]] = None,
    alignments: Optional[List[str]] = None,
    **pad_kwargs,
) -> str:
    """
    Convert a list of dicts into a Markdown table string.
    Auto-detects numeric columns if alignments not given.
    """
    if not dict_rows:
        return ''

    if fieldnames is None:
        fieldnames = list(dict_rows[0].keys())

    rows = [fieldnames]
    for d in dict_rows:
        rows.append([str(d.get(f, '')) for f in fieldnames])

    return to_markdown_table(rows, alignments=alignments, **pad_kwargs)


def auto_format_markdown_table(table_str: str, **kwargs: Any) -> str:
    """
    Auto-formats a markdown table.
    """

    rows = parse_markdown_table(table_str)
    return to_markdown_table(rows, **kwargs)
