from mdexec import markdown
from mdexec.markdown import parse_document, apply_updates, HtmlCommentBlock, CodeBlock
import pytest

from mdexec.markdown import parse_document, apply_updates


def md(text: str) -> str:
    """Helper to allow ``` instead of ``` in test strings."""
    # return text.replace("```", "```")
    return text


# ----------------------------
# Code Block Parsing
# ----------------------------


def test_simple_code_block():
    text = md("""\
``` python exec output=out-1
print("hello")
```
""")

    blocks = parse_document(text)
    assert len(blocks) == 1

    block = blocks[0]
    assert isinstance(block, CodeBlock)

    assert block.content == 'print("hello")'
    assert block.pre_content.endswith('\n')
    assert block.post_content.startswith('\n')

    assert block.options['language'] == 'python'
    assert block.options['python'] is True
    assert block.options['exec'] is True
    assert block.output_id == 'out-1'


def test_code_block_no_language_only_options():
    text = md("""\
``` exec output=my-block
x = 1
```
""")

    blocks = parse_document(text)
    block = blocks[0]

    assert block.options['exec'] is True
    assert block.options['output'] == 'my-block'
    assert block.options['language'] == 'exec'


def test_empty_code_block():
    text = md("""\
``` python
```
""")

    blocks = parse_document(text)
    block = blocks[0]

    assert block.content == ''


def test_multiple_code_blocks():
    text = md("""\
``` python
a = 1
```

some text

``` bash exec
echo hi
```
""")

    blocks = parse_document(text)
    assert len(blocks) == 2

    assert blocks[0].content == 'a = 1'
    assert blocks[1].content == 'echo hi'


# ----------------------------
# HTML Comment Blocks
# ----------------------------


def test_simple_comment_block():
    text = """\
<!-- id:foo -->
hello world
<!-- /id:foo -->
"""

    blocks = parse_document(text)
    assert len(blocks) == 1

    block = blocks[0]
    assert isinstance(block, HtmlCommentBlock)

    assert block.id == 'foo'
    assert block.content.strip() == 'hello world'


def test_comment_block_with_options():
    text = """\
<!-- id:bar key=value flag -->
data
<!-- /id:bar -->
"""

    blocks = parse_document(text)
    block = blocks[0]

    assert block.id == 'bar'
    assert block.options['key'] == 'value'
    assert block.options['flag'] is True


def test_inline_comment_block():
    text = """before <!-- id:x -->mid<!-- /id:x --> after"""

    blocks = parse_document(text)
    assert len(blocks) == 1

    block = blocks[0]
    assert block.content == 'mid'


# ----------------------------
# Mixed Blocks
# ----------------------------


def test_code_inside_comment_block():
    text = md("""\
<!-- id:outer -->
``` python
x = 1
```
<!-- /id:outer -->
""")

    blocks = parse_document(text)

    # Only ONE block (comment), code is inside content
    assert len(blocks) == 1
    block = blocks[0]

    assert isinstance(block, HtmlCommentBlock)
    assert 'x = 1' in block.content


def test_comment_and_code_separate():
    text = md("""\
<!-- id:out -->
result
<!-- /id:out -->

``` python exec output=out
print("hi")
```
""")

    blocks = parse_document(text)
    assert len(blocks) == 2

    assert isinstance(blocks[0], HtmlCommentBlock)
    assert isinstance(blocks[1], CodeBlock)


# ----------------------------
# Error Cases
# ----------------------------


def test_unclosed_code_block_raises():
    text = md("""\
``` python
print("oops")
""")

    with pytest.raises(ValueError):
        parse_document(text)


def test_unclosed_comment_block_raises():
    text = """\
<!-- id:bad -->
oops
"""

    with pytest.raises(ValueError):
        parse_document(text)


def test_comment_inside_code_block_is_ignored():
    text = md("""\
``` python
<!-- id:x -->
```
<!-- /id:x -->
""")

    blocks = parse_document(text)

    # Only the code block should exist
    assert len(blocks) == 1
    assert isinstance(blocks[0], CodeBlock)


# ----------------------------
# Apply Updates
# ----------------------------


def test_apply_updates_content():
    text = md("""\
``` python exec output=out
print("hi")
```

<!-- id:out -->
old
<!-- /id:out -->
""")

    blocks = parse_document(text)

    # mutate output block
    for b in blocks:
        if isinstance(b, HtmlCommentBlock) and b.id == 'out':
            b.content = 'new result'

    updated = apply_updates(text, blocks)

    assert 'new result' in updated
    assert 'old' not in updated


def test_apply_updates_preserves_unmodified_text():
    text = md("""\
start

``` python
x = 1
```

end
""")

    blocks = parse_document(text)
    updated = apply_updates(text, blocks)

    assert updated == text  # exact match


# ----------------------------
# Round Trip Safety
# ----------------------------


def test_round_trip_no_changes():
    text = md("""\
``` python
x = 42
```
""")

    blocks = parse_document(text)
    result = apply_updates(text, blocks)

    assert result == text
