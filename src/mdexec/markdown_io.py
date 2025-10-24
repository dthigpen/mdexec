from __future__ import annotations
from pathlib import Path
from markdown_it import MarkdownIt
from markdown_it.token import Token
import copy
import re
import shlex

from .types import CodeBlock, HtmlBlock


def query_blocks(md_text: str, id=None, ids=None, tag=None):
    ids_list = []
    if id is not None:
        ids_list.append(id)
    if ids is not None:
        ids_list.extend(ids)

    for block in extract_blocks(md_text):
        for i in ids_list:
            if block.id == i:
                yield block
        if tag is not None and block.vars.get('tag', None) == tag:
            yield block


def parse_info_string(info: str) -> Dict[str, Any]:
    """
    Parse the info string of a fenced code block.

    Example inputs:
        "python exec id=foo a=1"
        "bash mdexec output-id='bar' path=\"/tmp/test.sh\""

    Returns:
        {
            "lang": "python",
            "exec": True,
            "vars": {"id": "foo", "a": "1"}
        }
    """
    if not info:
        return {'lang': '', 'exec': False, 'vars': {}}

    # shlex handles quotes and splitting like a shell command
    try:
        parts = shlex.split(info)
    except ValueError:
        parts = info.split()

    if not parts:
        return {'lang': '', 'exec': False, 'vars': {}}
    lang = parts[0]
    vars_dict: Dict[str, str] = {}
    exec_ = False

    # process remaining tokens
    for part in parts[1:]:
        if part == 'exec':
            exec_ = True
            continue
        if '=' in part:
            key, value = part.split('=', 1)
            vars_dict[key] = value.strip('"\'')
        else:
            # allow flags like "exec output" (rare)
            vars_dict[part] = ''

    return {'lang': lang, 'exec': exec_, 'vars': vars_dict}


def parse_fence(token: Token) -> CodeBlock:
    if token.type != 'fence':
        raise ValueError(f'Code blocks must have a fence token')

    info_data = parse_info_string(token.info or '')
    executable = info_data.get('exec', False)
    lang = info_data['lang']
    vars_dict = info_data['vars']
    # normalize - to _
    vars_dict_snake = {k.replace('-', '_'): v for k, v in vars_dict.items()}
    own_id = vars_dict_snake.get('id', None)
    output_id = vars_dict_snake.get(
        'output_id', None
    )  # output this code block to another location

    # Determine type
    if executable:
        block_type = None
    elif output_id:
        block_type = 'input'
    elif own_id:
        block_type = 'output'

    block = CodeBlock(
        token=token,
        lang=lang,
        content=token.content.strip('\n'),
        id=own_id,
        output_id=output_id,
        # type=block_type,
        vars=vars_dict,
        executable=executable,
    )
    return block


def parse_html_comment_block(start_token: Token, end_token: Token, md_text: Token):
    start_line = start_token.map[0] + 1
    end_line = end_token.map[0] if end_token else start_line + 1
    content = md_text[start_line:end_line] if end_token else ''
    start_content = start_token.content.strip()

    m = re.match(r'<!--\s+/?id:(\S+)(.*)\s+-->', start_content)
    found_id = m.group(1)
    rest = m.group(2).strip()
    parsed = parse_info_string('lang ' + rest)
    vars = parsed.get('vars', {})
    if not found_id:
        raise ValueError(f'HTML comment block must have an ID: {start_content}')
    return HtmlBlock(
        start_token=start_token,
        end_token=end_token,
        # type=None,
        id=found_id,
        content=content,
    )


def extract_blocks(md_text: str):
    md = MarkdownIt('commonmark')
    tokens = md.parse(md_text)
    html_id_start_tokens = {}

    for token in tokens:
        if token.type in ('html_inline', 'html_block'):
            content = token.content.strip()
            if m := re.match(r'<!--\s+id:(\S+)(.*)\s+-->', content):
                found_id = m.group(1)
                html_id_start_tokens[found_id] = token
            elif m := re.match(r'<!--\s+/id:(\S+)\s+-->', content):
                found_id = m.group(1)
                start_token = html_id_start_tokens.pop(found_id, None)
                if not start_token:
                    raise ValueError(
                        f'Found html block end token without the start token: {content}'
                    )
                yield parse_html_comment_block(start_token, token, md_text)
        elif token.type == 'fence':
            yield parse_fence(token)
    # Handle unclosed html blocks?
    for token_id, start_token in html_id_start_tokens.items():
        yield parse_html_comment_block(start_token, None, md_text)


def replace_output_block(
    md_text: str, block_id: str, new_content: str, match_indent=True
) -> str:
    """Replace the output block (HTML or fenced code) with the given new_output."""

    blocks = extract_blocks(md_text)
    updated = False
    new_text = md_text

    for block in blocks:
        # reject if ids do not match or if its an executable codeblock
        if block.id != block_id:
            continue

        print(
            f'Block "{block.id}" of type {type(block)} exec={isinstance(block, CodeBlock) and block.executable}'
        )
        # handle code block replacement
        if isinstance(block, CodeBlock) and not block.executable:
            new_text = _replace_fence_content(
                block, new_text, new_content, match_indent=match_indent
            )
            updated = True
            break  # only replace first match
        elif isinstance(block, HtmlBlock):
            new_text = _replace_html_block_content(
                block, new_text, new_content, match_indent=match_indent
            )
            updated = True
            break
        return new_text, updated

    if not updated:
        raise ValueError(
            f'[error] Could not find tag or code block with id={block_id}.'
        )
    return new_text


def _replace_html_block_content(
    block: HtmlBlock, md_text: str, new_output: str, match_indent=False
) -> str:
    lines = md_text.splitlines()
    start_line = block.start_token.map[0]
    end_line = block.end_token.map[0]

    if not block.end_token:
        lines.insert(end_line, f'<!-- /id:{block.id} -->')
    # Compute indentation padding (optional but nice)
    indent = ''
    if match_indent:
        indent = _detect_indent(lines[start_line])
        new_output = _indent_text(new_output, indent)

    # Prepare replacement block content
    rendered_lines = new_output.splitlines()

    # Replace section in place
    new_text = '\n'.join(lines[: start_line + 1] + rendered_lines + lines[end_line:])
    return new_text


def _replace_fence_content(
    block: CodeBlock, md_text: str, new_content: str, match_indent=False
) -> str:
    # get the line numbers from the token
    # TODO verify they are not "off by one" in this context
    block_start, block_end, *_ = block.token.map
    code_start = block_start + 1
    code_end = block_end - 1
    if match_indent:
        indent = _detect_indent(block.content)
        new_output = _indent_text(new_output, indent)

    lines = md_text.splitlines()
    rendered_lines = new_content.splitlines()
    # Replace section in place
    new_text = '\n'.join(lines[:code_start] + rendered_lines + lines[code_end:])
    return new_text


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
