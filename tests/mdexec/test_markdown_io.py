from mdexec import markdown_io
from mdexec.markdown_io import (
    parse_blocks,
    render_blocks,
    break_block_full_content,
)
from mdexec.types import TextBlock, HtmlCommentBlock, CodeBlock

import pytest


def test_code_block():
    block = CodeBlock(
        pre_content='```bash\n', content='echo hello', post_content='\n```'
    )

    block.content += '\necho and goodbye'
    assert block.full_content == '```bash\necho hello\necho and goodbye\n```'


# @pytest.mark.skip
def test_render_blocks():
    input_md = """
# Some Title [foo](www.example.com)
Paragraph text here
```bash
echo hello
```
<!-- id:foo -->
Initial output
<!-- /id:foo -->
After text
"""
    blocks = parse_blocks(input_md)
    rendered = render_blocks(blocks)
    assert rendered == input_md


def test_consecutive_fences():
    input_md = """```bash
echo hello
```
```python
echo hello
```"""
    blocks = parse_blocks(input_md)
    assert len(blocks) == 2


def test_break_block_full_content():
    lines = [
        'aaaaaa',
        'bbbbbb',
        'cccccc',
        'dddddd',
        'eeeeee',
    ]
    pre, inner, post = break_block_full_content(lines)
    assert pre == 'aaaaaa\n'
    assert inner == 'bbbbbb\ncccccc\ndddddd'
    assert post == '\neeeeee'


# @pytest.mark.skip
def test_parse_blocks():
    input_md = """
# Some Title [foo](www.example.com)
Paragraph text here
```bash
echo hello
```
<!-- id:foo -->
Initial output
<!-- /id:foo -->
After text
"""
    blocks = parse_blocks(input_md)
    assert len(blocks) == 4
    block = blocks.pop(0)
    assert isinstance(block, TextBlock)
    assert (
        block.full_content
        == '\n# Some Title [foo](www.example.com)\nParagraph text here'
    )
    block = blocks.pop(0)
    assert isinstance(block, CodeBlock)
    assert block.full_content == '```bash\necho hello\n```'
    block = blocks.pop(0)
    assert isinstance(block, HtmlCommentBlock)
    assert block.full_content == '<!-- id:foo -->\nInitial output\n<!-- /id:foo -->'
    block = blocks.pop(0)
    assert isinstance(block, TextBlock)
    assert block.full_content == 'After text\n'
