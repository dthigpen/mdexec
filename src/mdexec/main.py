#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import Any
from markdown_it import MarkdownIt
from .executor import execute_code_block
from .types import CodeBlock
from .markdown_io import (
    parse_blocks,
    render_blocks,
)


def main():
    parser = argparse.ArgumentParser(
        description='Execute code blocks in a Markdown file and render results inline.'
    )
    parser.add_argument(
        'input_file', type=Path, help='Path to the Markdown file to execute'
    )
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='Optional path for the output Markdown file. If omitted, outputs to the input file',
    )

    args = parser.parse_args()

    input_md = args.input_file.read_text(encoding='utf-8')
    rendered_md = run_mdexec(input_md)

    output_path = args.output or args.input_file
    if rendered_md != input_md:
        output_path.write_text(rendered_md, encoding='utf-8')
    else:
        print('[info] No changes to save')


def run_mdexec(text: str) -> str:
    """
    Process a Markdown file, execute code blocks marked with 'mdexec',
    and inject or update output blocks in the Markdown.

    Args:
        path: Path to the input Markdown file.

    Returns:
        The rendered Markdown with code outputs inserted.
    """
    blocks = parse_blocks(text)
    for block in blocks:
        if not isinstance(block, CodeBlock) or not block.executable:
            continue
        try:
            own_id = block.id
            output_id = block.output_id
            if output_id is None:
                print(
                    f'[warn] Executable code block did not contain an output-id. Outputing result to console.'
                )
            info_str = ''
            if own_id:
                info_str += f'id={own_id}'
            if output_id:
                info_str += f'output_id={output_id}'
            if not info_str:
                info_str = '<anonymous>'
            print(
                f'[info] Running code block on line {block.token.map[0] + 1}: {block.pre_content.strip()}'
            )

            result = execute_code_block(block)
        except Exception as e:
            result = f'Error: {e}'
        if output_id:
            output_block = next(
                (
                    b
                    for b in blocks
                    if b.id is not None
                    and b.id.replace('-', '_') == output_id.replace('-', '_')
                ),
                None,
            )
            if not output_block:
                raise ValueError(
                    f'Code block specified id of output block that does not exist: {output_id}'
                )
            output_block.content = result
        else:
            print(result)
    return render_blocks(blocks)


if __name__ == '__main__':
    main()
