import pytest
from mdexec.tables import (
    pad_columns,
    parse_markdown_table,
    markdown_table_dictreader,
    to_markdown_table,
    dicts_to_markdown_table,
    _infer_alignments,
    auto_format_markdown_table,
)


def test_basic_padding():
    data = [
        ['Name', 'Age', 'City'],
        ['Alice', '30', 'Denver'],
        ['Bob', '9', 'LA'],
    ]
    padded = pad_columns(data)
    # Verify first column padded properly (left aligned)
    assert padded[0][0].startswith('Name')
    # Numeric column should be right-aligned
    assert padded[1][1].strip() == '30'
    assert padded[2][1].strip() == '9'
    # City column still aligned left
    assert padded[1][2].startswith(' Denver')


def test_no_separator_space():
    data = [['a', 'bb'], ['ccc', 'd']]
    padded = pad_columns(data, separator_space=False)
    # No leading space before second column
    assert not padded[0][1].startswith(' ')


def test_empty_input():
    assert pad_columns([]) == []


def test_auto_align_numeric():
    data = [['Item', 'Count', 'Price'], ['Apple', '5', '2.5'], ['Pear', '10', '12']]
    padded = pad_columns(data)
    # numeric columns should be right-aligned
    count_col_width = max(len(r[1]) for r in padded)
    assert all(r[1].rstrip() == r[1] or r[1].startswith(' ') for r in padded[1:])
    # rightmost numeric column should be right-aligned too
    assert all(r[2].strip().isdigit() or '.' in r[2].strip() for r in padded[1:])


def test_disable_auto_align_numeric():
    data = [['A', 'B'], ['1', '2.0'], ['3', '4']]
    padded = pad_columns(data, auto_align_numeric=False)
    row_strs = ['|'.join(r) for r in padded]
    assert row_strs[0] == 'A | B  '
    assert row_strs[1] == '1 | 2.0'
    assert row_strs[2] == '3 | 4  '


@pytest.mark.parametrize('align', ['left', 'right', 'center'])
def test_manual_alignment_modes(align):
    data = [['Col1', 'Col2'], ['A', 'B'], ['AAAA', 'BBBB']]
    padded = pad_columns(data, alignment=align, auto_align_numeric=False)
    row_strs = ['|'.join(r) for r in padded]
    if align == 'left':
        assert row_strs[0] == 'Col1 | Col2'
        assert row_strs[1] == 'A    | B   '
        assert row_strs[2] == 'AAAA | BBBB'
    elif align == 'right':
        assert row_strs[0] == 'Col1 | Col2'
        assert row_strs[1] == '   A |    B'
        assert row_strs[2] == 'AAAA | BBBB'
    elif align == 'center':
        assert row_strs[0] == 'Col1 | Col2'
        assert row_strs[1] == ' A   |  B  '
        assert row_strs[2] == 'AAAA | BBBB'


MD_TABLE = """
| Name  | Age | City  |
|-------|-----|-------|
| Alice | 30  | Denver|
| Bob   | 9   | LA    |
"""


def test_parse_markdown_table_basic():
    rows = parse_markdown_table(MD_TABLE)
    assert rows == [
        ['Name', 'Age', 'City'],
        ['Alice', '30', 'Denver'],
        ['Bob', '9', 'LA'],
    ]


def test_parse_markdown_table_ignores_separator_lines():
    md = """
    | A | B |
    |---|---|
    | 1 | 2 |
    """
    rows = parse_markdown_table(md)
    assert len(rows) == 2  # header + 1 data row
    assert rows[1] == ['1', '2']


def test_markdown_table_dictreader():
    dict_rows = markdown_table_dictreader(MD_TABLE)
    assert dict_rows == [
        {'Name': 'Alice', 'Age': '30', 'City': 'Denver'},
        {'Name': 'Bob', 'Age': '9', 'City': 'LA'},
    ]


def test_handles_missing_cells():
    md = """
    | A | B | C |
    |---|---|---|
    | 1 | 2 |
    | 3 | 4 | 5 |
    """
    dict_rows = markdown_table_dictreader(md)
    # Missing cells should become empty strings
    assert dict_rows[0] == {'A': '1', 'B': '2', 'C': ''}
    assert dict_rows[1] == {'A': '3', 'B': '4', 'C': '5'}


def test_empty_table_returns_empty_list():
    assert parse_markdown_table('') == []
    assert markdown_table_dictreader('') == []


def test_alignment_markers_basic():
    rows = [['Col1', 'Col2', 'Col3'], ['A', 'B', 'C']]
    md = to_markdown_table(rows, alignments=['left', 'center', 'right'])
    lines = md.splitlines()
    assert lines[1].startswith('| :---')
    assert ':---:' in lines[1]
    assert '---:' in lines[1]


def test_alignment_markers_defaults():
    rows = [['A', 'B'], ['abc', '2']]
    md = to_markdown_table(rows)
    assert '| :--- | ---: |' in md


def test_dicts_to_markdown_table_alignment():
    data = [{'Name': 'Alice', 'Age': 30}, {'Name': 'Bob', 'Age': 9}]
    md = dicts_to_markdown_table(data, alignments=['left', 'right'])
    lines = md.splitlines()
    assert ':---' in lines[1]  # left align first column
    assert '---:' in lines[1]  # right align second column


def test_partial_alignments_list():
    rows = [['A', 'B', 'C'], ['1', '2', '3']]
    md = to_markdown_table(rows, alignments=['center'])
    # Only first column gets alignment marker, rest fallback to ---
    assert ':---:' in md.splitlines()[1]
    assert md.splitlines()[1].count('---') >= 2


def test_infer_alignments_detects_numeric_columns():
    rows = [['Name', 'Age', 'Score'], ['Alice', '30', '98.5'], ['Bob', '9', '77']]
    aligns = _infer_alignments(rows)
    assert aligns == ['left', 'right', 'right']


def test_to_markdown_table_autoalign_numeric():
    rows = [['Item', 'Qty', 'Price'], ['Apple', '2', '1.50'], ['Banana', '10', '0.99']]
    md = to_markdown_table(rows)
    sep_line = md.splitlines()[1]
    assert '---:' in sep_line  # numeric columns right-aligned
    assert ':---' in sep_line  # text column left-aligned


def test_dicts_to_markdown_table_autoalign():
    data = [
        {'Name': 'Alice', 'Age': 30, 'City': 'Denver'},
        {'Name': 'Bob', 'Age': 9, 'City': 'LA'},
    ]
    md = dicts_to_markdown_table(data)
    sep_line = md.splitlines()[1]
    assert '---:' in sep_line  # numeric column right-aligned


def test_manual_alignment_overrides_autoalign():
    rows = [['A', 'B', 'C'], ['1', '2', '3']]
    md = to_markdown_table(rows, alignments=['center', 'center', 'center'])
    sep_line = md.splitlines()[1]
    assert sep_line.count(':---:') == 3


def test_auto_format_markdown_table():
    raw = """| name | age |
|--|--|
| alice | 5 |
| bob | 10 |"""

    expected = """| name  | age |
| :--- | ---: |
| alice |   5 |
| bob   |  10 |"""
    formatted = auto_format_markdown_table(raw, separator_space=False)
    assert formatted == expected


def test_separator_space_both_sides():
    data = [['A', 'B', 'C'], ['1', '22', '333']]
    padded = pad_columns(data, separator_space=True)
    for row in padded:
        assert row[0].endswith(' ')
        assert row[1].startswith(' ')
        assert row[1].endswith(' ')
        assert row[2].startswith(' ')


def test_separator_space_disabled():
    data = [['A', 'BB'], ['1', '22']]
    padded = pad_columns(data, separator_space=False)
    # No extra space around the cell
    for row in padded:
        for cell in row:
            assert not cell.startswith(' ')
            assert not cell.endswith(' ')
