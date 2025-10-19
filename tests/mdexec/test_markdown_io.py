from mdexec import markdown_io
from mdexec.markdown_io import replace_output_block

import pytest


def test_replace_output_block():
    input_md = """
# Some Title
Paragraph text here
<!-- output-id:foo -->
Initial output
<!-- /output-id:foo -->
After text
"""
    expected_output_md = """
# Some Title
Paragraph text here
<!-- output-id:foo -->
Changed output
<!-- /output-id:foo -->
After text
"""

    actual_output = markdown_io.replace_output_block(input_md, 'foo', 'Changed output')
    assert expected_output_md == actual_output

    # test that an end marker gets added below start marker
    input_md = """
# Some Title
Paragraph text here
<!-- output-id:foo -->
After text
"""
    expected_output_md = """
# Some Title
Paragraph text here
<!-- output-id:foo -->
Changed output
<!-- /output-id:foo -->
After text
"""
    actual_output = markdown_io.replace_output_block(input_md, 'foo', 'Changed output')
    assert expected_output_md == actual_output

    # test that an exception gets thrown if just the output tag is found
    input_md = """
# Some Title
Paragraph text here
<!-- /output-id:foo -->
After text
"""
    with pytest.raises(ValueError, match='Expected output block found with id.*'):
        markdown_io.replace_output_block(input_md, 'foo', 'Changed output')


def test_extract_mdexec_blocks():
    text = """
# Some Title
Paragraph text here
```bash
echo hello
```
<!-- output-id:foo -->
Initial output
<!-- /output-id:foo -->
After text
"""
    blocks = list(markdown_io.extract_mdexec_blocks(text))
    assert len(blocks) == 0

    # id by code block
    text = """
# Some Title
Paragraph text here
```bash mdexec key=value id=foo
echo hello
```
<!-- output-id:foo -->
Initial output
<!-- /output-id:foo -->
After text
"""
    blocks = list(markdown_io.extract_mdexec_blocks(text))
    assert len(blocks) == 1
    block = blocks[0]

    # id by html comment
    assert block.id == 'foo'
