from __future__ import annotations
from pathlib import Path
from markdown_it import MarkdownIt
from markdown_it.token import Token
import copy
import re
import shlex

from .types import CodeBlock, HtmlCommentBlock, TextBlock, Block


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


def parse_fence(
    token: Token, pre_content: str = '', content: str = '', post_content: str = ''
) -> CodeBlock:
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

    block = CodeBlock(
        token=token,
        language=lang,
        pre_content=pre_content,
        content=content,
        post_content=post_content,
        id=own_id,
        output_id=output_id,
        options=vars_dict,
        executable=executable,
    )
    return block


def parse_html_comment_info(comment: str) -> dict:
    m = re.match(r'<!--\s+id[:=](\S+)(.*)\s+-->', comment)
    found_id = m.group(1)
    rest = m.group(2).strip()
    parsed = parse_info_string('fakelang ' + rest)
    if not found_id:
        raise ValueError(f'HTML comment block must have an ID: {start_content}')
    return {'id': found_id, 'options': parsed.get('vars', {})}


def join(l: list):
    return '\n'.join(l)


def break_block_full_content(
    lines: list[str], pre_content_len=1, post_content_len=1
) -> tuple[str, str, str]:
    """Breaks into 1 line of pre-content, N lines of content, and 1 line of post-content"""
    pre_content = join(lines[:pre_content_len]) + '\n'
    inner_content = join(
        lines[pre_content_len:-post_content_len]
    )  # could add a nl here
    post_content = '\n' + join(lines[-post_content_len:])
    return pre_content, inner_content, post_content


def parse_blocks(md_text: str) -> list[Block]:
    md = MarkdownIt('commonmark')
    tokens = md.parse(md_text)
    html_id_start_tokens = {}
    # text_buffer = ''
    blocks = []
    md_lines = md_text.split('\n')
    text_buffer_start_line = 0

    def slice_lines(start_inc: int, end_exc: int) -> str:
        return '\n'.join(md_lines[start_inc:end_exc])

    def append_and_reset_text_buffer(end_at_exc: int):
        nonlocal text_buffer_start_line
        # if not already on this line
        if text_buffer_start_line != end_at_exc:
            text_buffer = slice_lines(text_buffer_start_line, end_at_exc)
            blocks.append(TextBlock(content=text_buffer))
        text_buffer_start_line = end_at_exc

    for token in tokens:
        raw_content = token.content
        if token.type in ('html_inline', 'html_block'):
            content = raw_content.strip()
            start, end = token.map
            if m := re.match(r'<!--\s+id:(\S+)(.*)\s+-->', content):
                found_id = m.group(1)
                html_id_start_tokens[found_id] = token
                # save off existing text buffer to a text block
                # and start new buffer for html block
                append_and_reset_text_buffer(start)
            elif m := re.match(r'<!--\s+/id:(\S+)\s+-->', content):
                found_id = m.group(1)
                start_token = html_id_start_tokens.pop(found_id, None)
                if not start_token:
                    raise ValueError(
                        f'Found html block end token without the start token: {content}'
                    )
                pre_content, inner_content, post_content = break_block_full_content(
                    md_lines[start_token.map[0] : end]
                )
                html_info = parse_html_comment_info(pre_content.strip())
                html_block = HtmlCommentBlock(
                    id=html_info.get('id', None),
                    options=html_info.get('options', {}),
                    pre_content=pre_content,
                    content=inner_content,
                    post_content=post_content,
                    start_token=start_token,
                    end_token=token,
                )

                text_buffer_start_line = end  # reset to end
                blocks.append(html_block)
        elif token.type == 'fence':
            start, end = token.map
            append_and_reset_text_buffer(start)
            text_buffer_start_line = end
            pre_content, inner_content, post_content = break_block_full_content(
                md_lines[start:end]
            )
            fence = parse_fence(
                token=token,
                pre_content=pre_content,
                content=inner_content,
                post_content=post_content,
            )
            blocks.append(fence)
        else:
            # do nothing, wait for eof or next token with a map to create a text block
            pass

    # NOTE could append closing tag here, but for now treat as warning
    if html_id_start_tokens:
        for token_id, token in html_id_start_tokens.items():
            print(
                f'[warn] Unclosed html comment block tag at line {token.map[0]}: {token.content.strip()}. Add a corresponding closing comment tag'
            )
    if text_buffer_start_line != len(md_lines):
        append_and_reset_text_buffer(len(md_lines))

    print(f'Parsed {len(blocks)} blocks')
    for i, b in enumerate(blocks):
        print(
            f'{i + 1} {type(b).__name__} id={b.id}\n  pre={b.pre_content}\n  content={b.content}\n  post={b.post_content}'
        )
    return blocks


def render_blocks(blocks: list[TextBlock]) -> str:
    contents = list(map(lambda b: b.full_content, blocks))
    return '\n'.join(contents)
