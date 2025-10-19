from __future__ import annotations
from pathlib import Path
from markdown_it import MarkdownIt
from markdown_it.token import Token
import copy
import re
import shlex

from .types import CodeBlock


def parse_info_string(info: str) -> Dict[str, Any]:
    """
    Parse the info string of a fenced code block.

    Example inputs:
        "python mdexec id=foo a=1"
        "bash mdexec output-id='bar' path=\"/tmp/test.sh\""

    Returns:
        {
            "lang": "python",
            "is_mdexec": True,
            "vars": {"id": "foo", "a": "1"}
        }
    """
    if not info:
        return {'lang': '', 'is_mdexec': False, 'vars': {}}

    # shlex handles quotes and splitting like a shell command
    try:
        parts = shlex.split(info)
    except ValueError:
        parts = info.split()

    if not parts:
        return {'lang': '', 'is_mdexec': False, 'vars': {}}

    lang = parts[0]
    vars_dict: Dict[str, str] = {}
    is_mdexec = False

    # process remaining tokens
    for part in parts[1:]:
        if part == 'mdexec':
            is_mdexec = True
            continue
        if '=' in part:
            key, value = part.split('=', 1)
            vars_dict[key] = value.strip('"\'')
        else:
            # allow flags like "mdexec output" (rare)
            vars_dict[part] = ''

    return {'lang': lang, 'is_mdexec': is_mdexec, 'vars': vars_dict}


def extract_mdexec_blocks(text: str) -> List[CodeBlock]:
    """
    Extracts mdexec-related code blocks (input or output) from markdown tokens.

    Args:
        text: The markdown formatted text.

    Returns:
        A list of CodeBlock instances.
    """
    md = MarkdownIt()
    tokens: List[Token] = md.parse(text)

    blocks: List[CodeBlock] = []
    for token in tokens:
        if token.type != 'fence':
            continue

        info_data = parse_info_string(token.info or '')
        lang = info_data['lang']
        vars_dict = info_data['vars']

        # Determine type
        block_type = 'output' if 'output-id' in vars_dict else 'input'

        if not info_data['is_mdexec']:
            continue

        block_id = vars_dict.get('id') or vars_dict.get('output-id')

        block = CodeBlock(
            token=token,
            lang=lang,
            code=token.content.strip('\n'),
            id=block_id,
            type=block_type,
            vars=vars_dict,
        )
        blocks.append(block)

    return blocks


def replace_output_block(
    md_text: str, block_id: str, new_output: str, match_indent=True
) -> str:
    """Replace the output block (HTML or fenced code) with the given new_output."""

    trailing_nl = md_text.endswith('\n')

    # Try HTML blocks first
    md_text, updated = _replace_html_output_block(
        md_text, block_id, new_output, match_indent=match_indent
    )

    # Then try fenced code blocks
    if not updated:
        md_text, updated = _replace_fenced_output_block(
            md_text, block_id, new_output, match_indent=match_indent
        )

    if updated and trailing_nl:
        md_text += '\n'
    if not updated:
        raise ValueError(
            f'[warning] Expected output block found with id {block_id}. E.g.  <!-- output-id:{block_id} --> or ```lang mdexec output-id={block_id}'
        )

    return md_text


def _replace_html_output_block(
    md_text: str, block_id: str, new_output: str, match_indent=True
) -> Tuple[str, bool]:
    """
    Replace or insert the rendered output for a given mdexec block ID.

    The function looks for:
        <!-- output-id:{block_id} -->
        ... (existing content) ...
        <!-- /output-id:{block_id} -->

    If the ending tag is not found, it will be inserted automatically.

    Args:
        md_text: Original markdown text.
        block_id: ID to locate in comment markers.
        new_output: Replacement markdown (typically fenced output).

    Returns:
        (updated_text, updated_flag).
    """
    md = MarkdownIt('commonmark')
    tokens = md.parse(md_text)
    updated = False

    start_line = None
    end_line = None

    # TODO may need to switch to regex and pair matches if too many token edge cases
    # Identify where this output section begins and ends
    for token in tokens:
        if token.type in ('html_inline', 'html_block'):
            content = token.content.strip()
            if content == f'<!-- output-id:{block_id} -->':
                start_line = token.map[0]
            elif content == f'<!-- /output-id:{block_id} -->':
                end_line = token.map[0]

    lines = md_text.splitlines()

    if start_line is not None and end_line is None:
        # Insert missing end marker right after start line
        end_line = start_line + 1
        lines.insert(end_line, f'<!-- /output-id:{block_id} -->')

    if start_line is not None and end_line is not None:
        # Compute indentation padding (optional but nice)
        indent = ''
        if match_indent:
            indent = _detect_indent(lines[start_line])
            new_output = _indent_text(new_output, indent)

        # Prepare replacement block content
        rendered_lines = new_output.splitlines()

        # Replace section in place
        md_text = '\n'.join(lines[: start_line + 1] + rendered_lines + lines[end_line:])
        updated = True
    return (md_text, updated)


def _replace_fenced_output_block(
    md_text: str, block_id: str, new_output: str, match_indent=True
) -> Tuple[str, bool]:
    """
    Replace output code blocks (```` ```output id=... ``` ````) matching the given block_id.
    Returns (updated_text, updated_flag).
    """
    blocks = extract_mdexec_blocks(md_text)
    updated = False
    new_text = md_text

    for block in blocks:
        if not block.is_output or block.id != block_id:
            continue

        # get the line numbers from  the token
        # TODO verify they are not "off by one" in this context
        block_start, block_end, *_ = block.token.map
        code_start = block_start + 1
        code_end = block_end - 1
        if match_indent:
            indent = _detect_indent(block.code)
            new_output = _indent_text(new_output, indent)

        lines = md_text.splitlines()
        rendered_lines = new_output.splitlines()
        # Replace section in place
        new_text = '\n'.join(lines[:code_start] + rendered_lines + lines[code_end:])
        updated = True
        break  # only replace first match

    return new_text, updated


def _detect_indent(text: str) -> str:
    """Detect the leading indentation of a block of text."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return ''
    first_line = lines[0]
    return re.match(r'\s*', first_line).group(0)


def _indent_text(text: str, indent: str) -> str:
    """Apply consistent indentation to each line of text."""
    return '\n'.join(
        f'{indent}{line}' if line.strip() else '' for line in text.splitlines()
    )
