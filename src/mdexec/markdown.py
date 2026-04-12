from __future__ import annotations
import re

FENCE_RE = re.compile(r'^(\s*)(`{3,})(.*)$', re.MULTILINE)
COMMENT_OPEN_RE = re.compile(r'<!--\s*id:([a-zA-Z0-9\-_]+)(.*?)-->')
COMMENT_CLOSE_RE = re.compile(r'<!--\s*/id:([a-zA-Z0-9\-_]+)\s*-->')


from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Block:
    pre_content: str = ''
    content: str = ''
    post_content: str = ''

    start_idx: int = -1
    end_idx: int = -1
    options: Dict[str, str] = field(default_factory=dict)

    @property
    def full_content(self):
        return str(self.pre_content) + str(self.content) + str(self.post_content)

    @property
    def id(self) -> str:
        return self.options.get('id', None)

    def get_option(self, key: str, default=None) -> Any:
        return {k.replace('-', '_'): v for k, v in self.options.items()}.get(
            key.replace('-', '_'), default
        )


@dataclass
class TextBlock(Block):
    pass


@dataclass
class HtmlCommentBlock(Block):
    pass


@dataclass
class CodeBlock(Block):
    @property
    def language(self) -> Optional[str]:
        return self.options.get('language')

    @property
    def executable(self) -> bool:
        return bool(self.options.get('exec', False))

    @property
    def full_content(self):

        pre = str(self.pre_content)
        con = str(self.content)
        post = str(self.post_content)
        if con and not post.startswith('\n'):
            post = '\n' + post
        return pre + con + post


def parse_options(raw: str):
    """
    Parses everything into options without stripping a "language" token.
    Example:
        "python exec output=foo"
    ->
        {
            "language": "python",
            "python": True,
            "exec": True,
            "output": "foo"
        }
    """
    options = {}
    parts = raw.strip().split()

    for i, part in enumerate(parts):
        if '=' in part:
            k, v = part.split('=', 1)
            options[k] = v
        else:
            options[part] = True
            if i == 0:
                options['language'] = part

    return options


def parse_document(text: str) -> list[Block]:
    blocks: list[Block] = []

    i = 0
    length = len(text)

    while i < length:
        fence_match = FENCE_RE.match(text, i)
        if fence_match:
            indent, fence, rest = fence_match.groups()
            options = parse_options(rest)

            open_start = fence_match.start()
            open_end = fence_match.end()

            # --- find closing fence ---
            search_pos = open_end
            while True:
                next_match = FENCE_RE.search(text, search_pos)
                if not next_match:
                    raise ValueError('Unclosed code block')

                if next_match.group(2) == fence:
                    break

                search_pos = next_match.end()

            close_start = next_match.start()
            close_end = next_match.end()

            # --- normalize boundaries ---

            # find first newline after opening fence
            first_newline = text.find('\n', open_end)
            if first_newline == -1:
                raise ValueError('Opening fence must end with newline')

            pre_end = first_newline + 1

            # closing fence must start at beginning of line
            if close_start > 0 and text[close_start - 1] != '\n':
                raise ValueError('Closing fence must be on its own line')

            # content ends right before that newline
            content_end = close_start - 1  # exclude newline before closing fence

            # handle empty block safely
            if content_end < pre_end:
                content = ''
                post_start = pre_end
            else:
                content = text[pre_end:content_end]
                post_start = content_end  # includes newline

            pre = text[open_start:pre_end]
            post = text[post_start:close_end]

            # Strip only ONE trailing newline from content if present
            if content.endswith('\n'):
                content = content[:-1]

            block = CodeBlock(
                pre_content=pre,
                content=content,
                post_content=post,
                start_idx=open_start,
                end_idx=close_end,
                options=options,
            )

            blocks.append(block)
            i = close_end
            continue

        # --- Comment block ---
        open_match = COMMENT_OPEN_RE.search(text, i)
        if open_match and open_match.start() == i:
            block_id = open_match.group(1)
            options = parse_options(open_match.group(2))

            close_match = COMMENT_CLOSE_RE.search(text, open_match.end())
            if not close_match:
                raise ValueError(f'Unclosed comment block: {block_id}')

            start = open_match.start()
            end = close_match.end()

            pre = text[start : open_match.end()]
            content = text[open_match.end() : close_match.start()]
            post = text[close_match.start() : end]
            if block_id:
                options['id'] = block_id
            block = HtmlCommentBlock(
                pre_content=pre,
                content=content,
                post_content=post,
                start_idx=start,
                end_idx=end,
                options=options,
            )

            blocks.append(block)
            i = end
            continue
        # advance safely
        i += 1

    # --- sort + overlap check ---
    blocks.sort(key=lambda b: b.start_idx)

    for i in range(1, len(blocks)):
        prev = blocks[i - 1]
        curr = blocks[i]

        if curr.start_idx < prev.end_idx:
            raise ValueError(
                f'Overlapping blocks detected:\n'
                f'- Prev: {prev.start_idx}-{prev.end_idx}\n'
                f'- Curr: {curr.start_idx}-{curr.end_idx}'
            )

    return blocks


def apply_updates(text: str, blocks: list[Block]) -> str:
    """
    Rebuilds the document using original text + updated blocks.

    Assumes:
    - blocks are based on original text
    - start_idx/end_idx are unchanged
    - blocks do not overlap
    """

    if not blocks:
        return text

    # ensure correct order
    blocks = sorted(blocks, key=lambda b: b.start_idx)

    result = []
    cursor = 0

    for block in blocks:
        # unchanged text before block
        result.append(text[cursor : block.start_idx])

        # updated block content
        result.append(block.full_content)

        cursor = block.end_idx

    # remaining tail
    result.append(text[cursor:])

    return ''.join(result)
